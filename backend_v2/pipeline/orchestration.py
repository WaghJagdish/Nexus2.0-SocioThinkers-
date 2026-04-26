import uuid
import base64
import logging
from typing import Dict, Any, Optional

from core.logging import get_logger
from services.speech_service import SpeechService
from services.form_filler import PDFFormFiller
from services.retrieval_service import SchemeRetriever
from agents.scheme_agent import SchemeNavigatorAgent
from core.domain import LanguageCode

logger = get_logger(__name__)

# Language code to Sarvam language code mapping
LANG_TO_SARVAM = {
    "hi": "hi-IN",
    "mr": "mr-IN",
    "en": "en-IN",
    "pa": "pa-IN",
    "ta": "ta-IN",
    "te": "te-IN",
    "kn": "kn-IN",
    "gu": "gu-IN",
    "bn": "bn-IN",
    "or": "or-IN",
    "ml": "ml-IN",
}


class SchemeOrchestrator:
    """
    Central pipeline managing the STT -> Graph -> TTS -> PDF flow.
    Coordinates voice service, retrieval, scheme agent, and form filler.
    """

    def __init__(
        self,
        voice_service: SpeechService,
        retriever: SchemeRetriever,
        scheme_agent: SchemeNavigatorAgent,
        form_filler: PDFFormFiller,
    ):
        self.voice_service = voice_service
        self.retriever = retriever
        self.scheme_agent = scheme_agent
        self.form_filler = form_filler

    async def run_voice_interaction(
        self,
        audio_input: bytes,
        user_context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Primary execution function for voice-based scheme interaction.
        Converts audio to intent, updates state, progresses the graph,
        and responds via voice.
        """
        thread_id = user_context.get("session_id", str(uuid.uuid4()))
        language = user_context.get("language_pref", "hi")
        sarvam_lang = LANG_TO_SARVAM.get(language, "hi-IN")
        lang_enum = LanguageCode(language) if language in [e.value for e in LanguageCode] else LanguageCode.HINDI

        # 1. Speech to Text (Sarvam AI)
        try:
            user_text = await self.voice_service.transcribe(audio_input, lang_enum)
            if not user_text:
                return {"error": "Audio parsing failed. Please try speaking clearly."}
        except Exception as e:
            logger.error(f"STT failed: {e}")
            return {"error": "Speech transcription failed."}

        logger.info(f"User Input ({thread_id}): {user_text}")

        # 2. Run through the graph
        result = await self.run_text_interaction(
            text_input=user_text,
            user_context=user_context,
        )

        # 3. Text to Speech Response
        ai_message = result.get("text_response", "")
        audio_response_b64 = None
        if ai_message:
            try:
                audio_bytes = await self.voice_service.synthesize(ai_message, lang_enum)
                if audio_bytes:
                    audio_response_b64 = base64.b64encode(audio_bytes).decode("utf-8")
            except Exception as e:
                logger.warning(f"TTS failed: {e}")

        result["audio_response_b64"] = audio_response_b64
        result["transcript"] = user_text
        return result

    async def run_text_interaction(
        self,
        text_input: str,
        user_context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Text-based scheme interaction. Handles RAG retrieval on first turn,
        then delegates to the scheme agent graph.
        """
        thread_id = user_context.get("session_id", str(uuid.uuid4()))
        language = user_context.get("language_pref", "hi")
        user_profile = user_context.get("profile", {})

        # Check if we need to do RAG retrieval (first turn or no scheme targeted)
        status = self.scheme_agent.get_thread_status(thread_id)
        target_scheme = None

        if not status or not status.get("current_step") or status["current_step"] == "pending":
            # First interaction — perform RAG retrieval to identify scheme
            user_state = user_profile.get("state", "Central")
            user_land = float(user_profile.get("land_area", 0))

            try:
                docs = await self.retriever.retrieve_relevant_schemes(
                    query=text_input,
                    user_state=user_state,
                    user_land_size=user_land,
                )
                if docs:
                    target_scheme = docs[0]  # Top match
                    logger.info(
                        f"RAG identified scheme: {target_scheme.get('name', 'unknown')}"
                    )
            except Exception as e:
                logger.warning(f"RAG retrieval failed, continuing without scheme: {e}")

        # Run graph step
        result = await self.scheme_agent.run_graph_step(
            thread_id=thread_id,
            user_message=text_input,
            target_scheme=target_scheme,
            language=language,
            user_profile=user_profile,
        )

        return {
            "thread_id": result["thread_id"],
            "status": result["current_step"],
            "text_response": result.get("last_ai_message", ""),
            "collected_data": result.get("collected_data", {}),
            "missing_fields": result.get("missing_fields", []),
            "is_eligible": result.get("is_eligible", False),
            "form_pdf_path": result.get("form_pdf_path", ""),
            "messages": result.get("messages", []),
        }

    async def get_status(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve the exact execution state of a conversation thread."""
        return self.scheme_agent.get_thread_status(thread_id)

    async def confirm(self, thread_id: str, approved: bool) -> Dict[str, Any]:
        """Resume a paused thread after HITL confirmation."""
        return await self.scheme_agent.confirm_submission(thread_id, approved)
