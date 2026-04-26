import asyncio
import base64
from typing import Optional, Any, List
from uuid import uuid4

from fastapi import APIRouter, UploadFile, Form, File, HTTPException, BackgroundTasks
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, SystemMessage

from core.logging import get_logger
from core.exceptions import (
    ApplicationException,
    ValidationException,
    TranscriptionException,
    ErrorCode,
)
from core.domain import LanguageCode, ProcessingRequest, GeoLocation
from core.container import get_container
from services.speech_service import SpeechService
from agents.crop_agent import CropSowingAgent, CropRecommendationRequest
from agents.scheme_agent import SchemeNavigatorAgent, SchemeQueryRequest

MAX_AUDIO_BYTES = 10 * 1024 * 1024  # 10 MB

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1", tags=["agriculture"])


class AdviceResponse(BaseModel):
    session_id: str
    status: str
    response_text: str
    response_audio_url: Optional[str] = None
    recommended_crop: Optional[str] = None
    recommendations: Optional[List[dict]] = None
    matched_schemes: Optional[list] = None
    gis_data: Optional[dict] = None
    generated_pdf_url: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    version: str
    agents_loaded: int = 0
    services: dict


@router.post("/voice/sync", response_model=AdviceResponse)
async def process_voice(
    background_tasks: BackgroundTasks,
    audio_file: UploadFile = File(...),
    user_id: str = Form(...),
    latitude: float = Form(0.0),
    longitude: float = Form(0.0),
    device_language: str = Form("hi"),
    context: str = Form(None),
):
    session_id = str(uuid4())
    logger.info(f"[{session_id}] Voice input: user={user_id}, lang={device_language}")

    try:
        if device_language not in [e.value for e in LanguageCode]:
            raise ValidationException(f"Unsupported language: {device_language}")

        language = LanguageCode(device_language)
        audio_bytes = await audio_file.read()

        if not audio_bytes:
            raise ValidationException("Audio file is empty")
        if len(audio_bytes) > MAX_AUDIO_BYTES:
            raise ValidationException(f"Audio file exceeds {MAX_AUDIO_BYTES // (1024*1024)} MB limit")

        container = get_container()
        speech_service: SpeechService = await container.get("speech_service")

        logger.info(f"[{session_id}] Transcribing audio...")
        transcript = await speech_service.transcribe(audio_bytes, language)

        if not transcript:
            raise TranscriptionException("Transcription produced empty result")
            
        if context:
            transcript = f"Context: {context}\nUser Question: {transcript}"

        logger.info(f"[{session_id}] Transcript: {transcript[:100]}...")

        crop_agent: CropSowingAgent = await container.get("crop_agent")
        scheme_agent: SchemeNavigatorAgent = await container.get("scheme_agent")
        gis_service = await container.get("gis_service")

        # Fetch soil data once (crop_agent also needs it but will hit cache)
        soil_data = await gis_service.fetch_soil_data(latitude, longitude)

        crop_request = CropRecommendationRequest(
            latitude=latitude,
            longitude=longitude,
            language=language,
        )
        scheme_request = SchemeQueryRequest(
            query=transcript,
            user_id=user_id,
            language=language,
        )

        # Parallelize independent agent calls
        recommendations, schemes = await asyncio.gather(
            crop_agent.recommend_crops(crop_request),
            scheme_agent.search_schemes(scheme_request),
        )

        # Generate conversational response
        llm_service = await container.get("llm_service")
        schemes_ctx = "\n".join([f"- {s.name}: {s.benefits}" for s in schemes]) if schemes else "None found."
        crop_ctx = f"{recommendations[0].crop_name.value} ({recommendations[0].reasoning})" if recommendations else "None"
        
        prompt = f"""
        The user asked: "{transcript}"
        
        Contextual Data:
        - Crop Recommendation: {crop_ctx}
        - Relevant Schemes:
        {schemes_ctx}
        
        Answer the user's question directly and concisely. If they asked about a scheme, explain it. If they asked about crops, explain the recommendation. Keep the response under 4 sentences.
        CRITICAL: Respond STRICTLY in the {language.name} language.
        """
        response_text = await llm_service.invoke([
            SystemMessage(content=f"You are a helpful agricultural AI assistant. You must respond strictly in {language.name}."),
            HumanMessage(content=prompt)
        ])

        audio_url = None
        try:
            logger.info(f"[{session_id}] Synthesizing response...")
            audio_bytes_out = await speech_service.synthesize(response_text, language)
            audio_url = f"data:audio/wav;base64,{base64.b64encode(audio_bytes_out).decode()}"
            logger.info(f"[{session_id}] Audio synthesized: {len(audio_bytes_out)} bytes")
        except Exception as e:
            logger.warning(f"[{session_id}] TTS failed: {e}")

        # Log interaction in background
        try:
            interaction_repo = await container.get("interaction_repository")
            background_tasks.add_task(
                interaction_repo.create,
                user_id=user_id,
                session_id=session_id,
                query_text=transcript,
                response_text=response_text,
                agent_used="voice_sync",
            )
        except Exception as e:
            logger.warning(f"[{session_id}] Failed to queue interaction log: {e}")

        recs_dicts = [r.to_dict() for r in recommendations] if recommendations else None

        return AdviceResponse(
            session_id=session_id,
            status="success",
            response_text=response_text,
            response_audio_url=audio_url,
            recommended_crop=recommendations[0].crop_name.value if recommendations else None,
            recommendations=recs_dicts,
            matched_schemes=[s.to_dict() for s in schemes] if schemes else None,
            gis_data=soil_data.to_dict() if soil_data else None,
        )

    except ApplicationException as e:
        logger.error(f"[{session_id}] Application error: {e.message}")
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"[{session_id}] Unexpected error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


class TextQueryRequest(BaseModel):
    user_id: str
    text: str
    latitude: float = 0.0
    longitude: float = 0.0
    device_language: str = "hi"

@router.post("/text/query", response_model=AdviceResponse)
async def process_text(
    request_data: TextQueryRequest,
    background_tasks: BackgroundTasks,
):
    user_id = request_data.user_id
    text = request_data.text
    latitude = request_data.latitude
    longitude = request_data.longitude
    device_language = request_data.device_language

    session_id = str(uuid4())
    logger.info(f"[{session_id}] Text query: user={user_id}, lang={device_language}")

    try:
        if device_language not in [e.value for e in LanguageCode]:
            raise ValidationException(f"Unsupported language: {device_language}")

        if not text or not text.strip():
            raise ValidationException("Query text cannot be empty")

        language = LanguageCode(device_language)

        container = get_container()
        crop_agent: CropSowingAgent = await container.get("crop_agent")
        scheme_agent: SchemeNavigatorAgent = await container.get("scheme_agent")
        gis_service = await container.get("gis_service")

        # Pre-fetch soil data so crop_agent hits cache on its internal call
        soil_data = await gis_service.fetch_soil_data(latitude, longitude)

        crop_request = CropRecommendationRequest(
            latitude=latitude,
            longitude=longitude,
            language=language,
        )
        scheme_request = SchemeQueryRequest(
            query=text,
            user_id=user_id,
            language=language,
        )

        # Parallelize independent agent calls
        recommendations, schemes = await asyncio.gather(
            crop_agent.recommend_crops(crop_request),
            scheme_agent.search_schemes(scheme_request),
        )

        # Generate conversational response
        llm_service = await container.get("llm_service")
        schemes_ctx = "\n".join([f"- {s.name}: {s.benefits}" for s in schemes]) if schemes else "None found."
        crop_ctx = f"{recommendations[0].crop_name.value} ({recommendations[0].reasoning})" if recommendations else "None"
        
        prompt = f"""
        The user asked: "{text}"
        
        Contextual Data:
        - Crop Recommendation: {crop_ctx}
        - Relevant Schemes:
        {schemes_ctx}
        
        Answer the user's question directly and concisely. If they asked about a scheme, explain it. If they asked about crops, explain the recommendation. Keep the response under 4 sentences.
        CRITICAL: Respond STRICTLY in the {language.name} language.
        """
        response_text = await llm_service.invoke([
            SystemMessage(content=f"You are a helpful agricultural AI assistant. You must respond strictly in {language.name}."),
            HumanMessage(content=prompt)
        ])

        audio_url = None
        try:
            logger.info(f"[{session_id}] Synthesizing response audio for text query...")
            speech_service = await container.get("speech_service")
            audio_bytes_out = await speech_service.synthesize(response_text, language)
            audio_url = f"data:audio/wav;base64,{base64.b64encode(audio_bytes_out).decode()}"
            logger.info(f"[{session_id}] Audio synthesized: {len(audio_bytes_out)} bytes")
        except Exception as e:
            logger.warning(f"[{session_id}] TTS failed: {e}")

        # Log interaction in background
        try:
            interaction_repo = await container.get("interaction_repository")
            background_tasks.add_task(
                interaction_repo.create,
                user_id=user_id,
                session_id=session_id,
                query_text=text,
                response_text=response_text,
                agent_used="text_query",
            )
        except Exception as e:
            logger.warning(f"[{session_id}] Failed to queue interaction log: {e}")

        recs_dicts = [r.to_dict() for r in recommendations] if recommendations else None

        return AdviceResponse(
            session_id=session_id,
            status="success",
            response_text=response_text,
            response_audio_url=audio_url,
            recommended_crop=recommendations[0].crop_name.value if recommendations else None,
            recommendations=recs_dicts,
            matched_schemes=[s.to_dict() for s in schemes] if schemes else None,
            gis_data=soil_data.to_dict() if soil_data else None,
        )

    except ApplicationException as e:
        logger.error(f"[{session_id}] Application error: {e.message}")
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"[{session_id}] Unexpected error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/health", response_model=HealthResponse)
async def health_check():
    container = get_container()

    try:
        db_service = await container.get("database_service")
        db_healthy = await db_service.health_check()
    except Exception as e:
        logger.warning(f"Database health check failed: {e}")
        db_healthy = False

    return HealthResponse(
        status="healthy",
        version="2.0.0",
        agents_loaded=2,
        services={
            "database": "healthy" if db_healthy else "unhealthy",
            "llm": "healthy",
            "cache": "healthy",
        },
    )
