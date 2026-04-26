import base64
from typing import Dict, Any, Optional, List
from uuid import uuid4

from fastapi import APIRouter, UploadFile, Form, File, HTTPException
from pydantic import BaseModel

from core.logging import get_logger
from core.container import get_container
from core.exceptions import ApplicationException, ValidationException

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/scheme", tags=["scheme-form-filling"])


# ---------------------------------------------------------------------------
# Request / Response Models
# ---------------------------------------------------------------------------

class SchemeChatRequest(BaseModel):
    thread_id: Optional[str] = None
    user_id: str
    message: str
    scheme_id: Optional[str] = None
    scheme_data: Optional[Dict[str, Any]] = None
    language: str = "hi"
    user_state: Optional[str] = None
    land_area: Optional[float] = None


class SchemeChatResponse(BaseModel):
    thread_id: str
    status: str
    text_response: str
    audio_response_b64: Optional[str] = None
    collected_data: Dict[str, Any] = {}
    missing_fields: List[str] = []
    is_eligible: bool = False
    form_pdf_path: Optional[str] = None
    messages: List[Dict[str, str]] = []


class ConfirmRequest(BaseModel):
    thread_id: str
    approved: bool


class ConfirmResponse(BaseModel):
    thread_id: str
    current_step: str
    last_ai_message: str


class ThreadStatusResponse(BaseModel):
    current_step: str
    collected_data: Dict[str, Any] = {}
    missing_fields: List[str] = []
    form_pdf_path: Optional[str] = None
    is_eligible: bool = False


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/chat", response_model=SchemeChatResponse)
async def scheme_chat(request: SchemeChatRequest):
    """
    Multi-turn conversational scheme form-filling endpoint.
    On each call the user sends a message and receives the next question
    or a status update (form generated, rejected, etc.).
    """
    thread_id = request.thread_id or str(uuid4())

    try:
        container = get_container()
        orchestrator = await container.get("scheme_orchestrator")

        user_context = {
            "session_id": thread_id,
            "language_pref": request.language,
            "profile": {
                "user_id": request.user_id,
                "state": request.user_state or "",
                "land_area": request.land_area or 0,
            },
        }

        # If scheme_data is provided directly, pass it
        # Otherwise the orchestrator will do RAG retrieval
        if request.scheme_data:
            result = await orchestrator.scheme_agent.run_graph_step(
                thread_id=thread_id,
                user_message=request.message,
                target_scheme=request.scheme_data,
                language=request.language,
                user_profile=user_context["profile"],
            )
            return SchemeChatResponse(
                thread_id=result["thread_id"],
                status=result["current_step"],
                text_response=result.get("last_ai_message", ""),
                collected_data=result.get("collected_data", {}),
                missing_fields=result.get("missing_fields", []),
                is_eligible=result.get("is_eligible", False),
                form_pdf_path=result.get("form_pdf_path"),
                messages=result.get("messages", []),
            )

        result = await orchestrator.run_text_interaction(
            text_input=request.message,
            user_context=user_context,
        )

        return SchemeChatResponse(
            thread_id=result.get("thread_id", thread_id),
            status=result.get("status", "unknown"),
            text_response=result.get("text_response", ""),
            collected_data=result.get("collected_data", {}),
            missing_fields=result.get("missing_fields", []),
            is_eligible=result.get("is_eligible", False),
            form_pdf_path=result.get("form_pdf_path"),
            messages=result.get("messages", []),
        )

    except ApplicationException as e:
        logger.error(f"Application error in scheme chat: {e.message}")
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Unexpected error in scheme chat: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/voice", response_model=SchemeChatResponse)
async def scheme_voice(
    audio_file: UploadFile = File(...),
    user_id: str = Form(...),
    thread_id: str = Form(None),
    language: str = Form("hi"),
    user_state: str = Form(None),
    land_area: float = Form(0.0),
    scheme_id: str = Form(None),
):
    """
    Voice-based scheme form-filling. Accepts audio, transcribes it,
    runs through the graph, and returns text + audio response.
    """
    tid = thread_id or str(uuid4())

    try:
        container = get_container()
        orchestrator = await container.get("scheme_orchestrator")

        audio_bytes = await audio_file.read()
        if not audio_bytes:
            raise ValidationException("Audio file is empty")

        user_context = {
            "session_id": tid,
            "language_pref": language,
            "profile": {
                "user_id": user_id,
                "state": user_state or "",
                "land_area": land_area,
            },
        }

        result = await orchestrator.run_voice_interaction(
            audio_input=audio_bytes,
            user_context=user_context,
        )

        if "error" in result:
            raise HTTPException(status_code=422, detail=result["error"])

        return SchemeChatResponse(
            thread_id=result.get("thread_id", tid),
            status=result.get("status", "unknown"),
            text_response=result.get("text_response", ""),
            audio_response_b64=result.get("audio_response_b64"),
            collected_data=result.get("collected_data", {}),
            missing_fields=result.get("missing_fields", []),
            is_eligible=result.get("is_eligible", False),
            form_pdf_path=result.get("form_pdf_path"),
            messages=result.get("messages", []),
        )

    except ApplicationException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in scheme voice: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/status/{thread_id}", response_model=ThreadStatusResponse)
async def get_status(thread_id: str):
    """Retrieves the exact execution state of a conversation thread."""
    try:
        container = get_container()
        orchestrator = await container.get("scheme_orchestrator")

        status = await orchestrator.get_status(thread_id)
        if not status:
            raise HTTPException(status_code=404, detail="Thread not found")

        return ThreadStatusResponse(**status)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/confirm", response_model=ConfirmResponse)
async def confirm_submission(req: ConfirmRequest):
    """
    Resumes a thread that is paused at form_generated step.
    Injects the user's boolean approval decision.
    """
    try:
        container = get_container()
        orchestrator = await container.get("scheme_orchestrator")

        result = await orchestrator.confirm(req.thread_id, req.approved)

        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])

        return ConfirmResponse(
            thread_id=result["thread_id"],
            current_step=result["current_step"],
            last_ai_message=result["last_ai_message"],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error confirming submission: {e}")
        raise HTTPException(status_code=500, detail=str(e))
