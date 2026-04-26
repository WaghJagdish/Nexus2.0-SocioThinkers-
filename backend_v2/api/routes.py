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
    context: Optional[str] = Form(None),
):
    audio_bytes = await audio_file.read()
    if not audio_bytes:
        raise ValidationException("Audio file is empty")
    if len(audio_bytes) > MAX_AUDIO_BYTES:
        raise ValidationException(f"Audio file exceeds {MAX_AUDIO_BYTES // (1024*1024)} MB limit")

    language = device_language
    session_id = str(uuid4())
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
    weather_service = await container.get("weather_service")
    crop_kb = await container.get("crop_knowledge_base")

    # Parallel fetch: soil + weather + crop recommendations + schemes + RAG knowledge
    soil_data_task = gis_service.fetch_soil_data(latitude, longitude)
    weather_data_task = weather_service.fetch_weather(latitude, longitude)

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

    recommendations_task = crop_agent.recommend_crops(crop_request)
    schemes_task = scheme_agent.search_schemes(scheme_request)

    # RAG: Extract likely crop keywords from transcript and retrieve knowledge
    rag_context = ""
    if crop_kb:
        from services.crop_analysis_service import _normalize_crop_name
        # Simple keyword extraction for common crops
        common_crops = [
            "wheat", "rice", "paddy", "maize", "corn", "cotton", "sugarcane", "sugar cane",
            "groundnut", "peanut", "soybean", "mustard", "gram", "chickpea", "pea", "arhar",
            "tur", "lentil", "moong", "urad", "barley", "millet", "bajra", "jowar", "sorghum",
            "tomato", "potato", "onion", "brinjal", "cauliflower", "cabbage", "chilli",
            "banana", "mango", "citrus", "orange", "apple", "grape", "papaya",
        ]
        mentioned = []
        t_lower = transcript.lower()
        for crop in common_crops:
            if crop in t_lower:
                norm = _normalize_crop_name(crop)
                if norm:
                    mentioned.append(norm)
        # Also try to detect disease mentions
        disease_keywords = ["disease", "pest", "fungus", "rot", "wilt", "rust", "blight", "mildew", "borer"]
        has_disease = any(kw in t_lower for kw in disease_keywords)
        if mentioned:
            for mc in mentioned[:2]:
                rag_knowledge = crop_kb.retrieve(mc, None if not has_disease else "general")
                if rag_knowledge:
                    top = rag_knowledge[0]
                    rag_context += (
                        f"\nCrop: {mc.title()} — Disease: {top.get('disease','N/A')}, "
                        f"Treatment: {top.get('treatment','N/A')}, "
                        f"Fertilizer: {top.get('fertilizer','N/A')}, "
                        f"Organic: {top.get('organic','N/A')}, "
                        f"Preventive: {top.get('preventive','N/A')}."
                    )
                    price = crop_kb.get_price(mc)
                    harvest = crop_kb.get_harvest(mc)
                    if price:
                        rag_context += f" Market price: ₹{price} per quintal."
                    if harvest:
                        rag_context += f" Harvest time: {harvest}."

    soil_data, weather_data, recommendations, schemes = await asyncio.gather(
        soil_data_task, weather_data_task, recommendations_task, schemes_task,
    )

    logger.info(
        f"[{uuid4()}] Agents responded: crops={len(recommendations)}, schemes={len(schemes)}"
    )

    # Generate exact, structured response using all context
    llm_service = await container.get("llm_service")
    system_prompt = (
        "You are KisanSetu, an expert agricultural advisor for Indian farmers. "
        "Your answers must be EXACT, FACTUAL, and directly based on the provided data. "
        "Never guess or hallucinate. Use the soil, weather, crop recommendations, scheme info, and RAG knowledge provided. "
        "If weather data is available, mention current conditions. "
        "If RAG knowledge mentions a disease, give the exact treatment steps and recommended pesticide/fertilizer. "
        "Keep responses concise (under 120 words), use bullet points for clarity, and speak in the farmer's language."
    )

    user_prompt = f"""Farmer's voice question (transcribed): "{transcript}"

Farmer location: Latitude {latitude}, Longitude {longitude}

=== SOIL DATA ===
{soil_data}

=== WEATHER DATA ===
{weather_data}

=== CROP RECOMMENDATIONS ===
{recommendations}

=== RELEVANT GOVERNMENT SCHEMES ===
{schemes}

=== RAG CROP KNOWLEDGE ===
{rag_context if rag_context else 'No specific crop disease knowledge matched.'}

Instructions:
1. Answer the farmer's question directly and exactly.
2. Reference their soil type and weather if relevant.
3. If they asked about a specific crop disease or pest, give the EXACT treatment from RAG knowledge.
4. Mention any relevant government schemes with next steps.
5. Response must be in {language} language.
6. Keep it under 120 words, factual, no fluff.
"""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ]
    response_text = await llm_service.invoke(messages, temperature=0.3)

    # Synthesize voice response
    audio_url = None
    try:
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
