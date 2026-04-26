import base64
import hashlib
from typing import Optional
import io
import asyncio

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from core.config import Settings
from core.logging import get_logger
from core.exceptions import TranscriptionException, SynthesisException
from services.cache_service import CacheService
from core.domain import LanguageCode

logger = get_logger(__name__)

SARVAM_BASE_URL = "https://api.sarvam.ai"

LANGUAGE_CODE_MAP = {
    LanguageCode.HINDI: "hi-IN",
    LanguageCode.MARATHI: "mr-IN",
    LanguageCode.ENGLISH: "en-IN",
    LanguageCode.PUNJABI: "pa-IN",
    LanguageCode.TAMIL: "ta-IN",
    LanguageCode.TELUGU: "te-IN",
    LanguageCode.KANNADA: "kn-IN",
    LanguageCode.GUJARATI: "gu-IN",
    LanguageCode.BENGALI: "bn-IN",
    LanguageCode.ODIA: "or-IN",
    LanguageCode.MALAYALAM: "ml-IN",
}


class SpeechService:
    def __init__(self, settings: Settings, cache: CacheService):
        self.settings = settings
        self.cache = cache

    def _get_headers(self) -> dict[str, str]:
        return {"api-subscription-key": self.settings.SARVAM_API_KEY}

    def _get_language_code(self, lang: LanguageCode) -> str:
        return LANGUAGE_CODE_MAP.get(lang, "hi-IN")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def transcribe(
        self,
        audio_bytes: bytes,
        language: LanguageCode = LanguageCode.HINDI,
    ) -> str:
        lang_code = self._get_language_code(language)
        cache_key = f"transcription_{hashlib.md5(audio_bytes).hexdigest()}_{lang_code}"

        cached = await self.cache.get("transcription", audio_hash=cache_key)
        if cached:
            logger.info(f"Transcription cache hit for {lang_code}")
            return cached

        try:
            # Detect actual audio format from magic bytes for proper filename
            if audio_bytes[:4] == b"\x1aE\xdf\xa3":
                filename, mime = "audio.webm", "audio/webm"
            elif audio_bytes[:4] == b"OggS":
                filename, mime = "audio.ogg", "audio/ogg"
            elif audio_bytes[:4] == b"RIFF":
                filename, mime = "audio.wav", "audio/wav"
            else:
                filename, mime = "audio.webm", "audio/webm"

            async with httpx.AsyncClient(timeout=self.settings.SARVAM_TIMEOUT) as client:
                response = await client.post(
                    f"{SARVAM_BASE_URL}/speech-to-text",
                    headers=self._get_headers(),
                    files={"file": (filename, io.BytesIO(audio_bytes), mime)},
                    data={
                        "language_code": lang_code,
                        "model": "saarika:v2.5",
                        "with_timestamps": "false",
                    },
                )
                response.raise_for_status()
                result = response.json()

                transcript = result.get("transcript", "")
                if not transcript:
                    raise TranscriptionException("Empty transcript from Sarvam API")

                await self.cache.set(
                    "transcription",
                    transcript,
                    ttl=86400,
                    audio_hash=cache_key,
                )
                logger.info(f"Transcription completed: {len(transcript)} chars")
                return transcript

        except httpx.TimeoutException as e:
            logger.error(f"Transcription timeout after {self.settings.SARVAM_TIMEOUT}s")
            raise TranscriptionException(f"Transcription timeout: {e}")
        except httpx.HTTPStatusError as e:
            logger.error(f"Transcription HTTP error: {e.status_code}")
            raise TranscriptionException(f"Transcription service error: {e.response.text}")
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            raise TranscriptionException(f"Transcription failed: {e}")

    def _split_text(self, text: str, max_chars: int = 500) -> list[str]:
        if len(text) <= max_chars:
            return [text]

        chunks = []
        while text:
            chunk = text[:max_chars]
            last_break = max(
                chunk.rfind("."),
                chunk.rfind("।"),
                chunk.rfind("?"),
                chunk.rfind("!"),
            )
            if last_break > max_chars // 2:
                chunk = text[:last_break + 1]
            chunks.append(chunk.strip())
            text = text[len(chunk):].strip()
        return chunks

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def synthesize(
        self,
        text: str,
        language: LanguageCode = LanguageCode.HINDI,
    ) -> bytes:
        lang_code = self._get_language_code(language)
        cache_key = f"synthesis_{hashlib.md5(text.encode('utf-8')).hexdigest()}_{lang_code}"

        cached = await self.cache.get("synthesis", text_hash=cache_key)
        if cached:
            logger.info(f"Synthesis cache hit for {lang_code}")
            return base64.b64decode(cached)

        chunks = self._split_text(text, max_chars=500)
        all_audio: list[bytes] = []

        try:
            async with httpx.AsyncClient(timeout=self.settings.SARVAM_TIMEOUT) as client:
                for idx, chunk in enumerate(chunks):
                    logger.info(f"Processing chunk {idx + 1}/{len(chunks)}")

                    payload = {
                        "inputs": [chunk],
                        "target_language_code": lang_code,
                        "speaker": "ritu",
                        "model": "bulbul:v3",
                        "enable_preprocessing": True,
                    }

                    response = await client.post(
                        f"{SARVAM_BASE_URL}/text-to-speech",
                        headers={**self._get_headers(), "Content-Type": "application/json"},
                        json=payload,
                    )
                    response.raise_for_status()
                    result = response.json()

                    audios = result.get("audios", [])
                    if audios:
                        audio_bytes = base64.b64decode(audios[0])
                        all_audio.append(audio_bytes)
                    else:
                        logger.warning(f"Chunk {idx + 1} returned no audio")

            if not all_audio:
                raise SynthesisException("No audio chunks generated")

            combined_audio = b"".join(all_audio)
            encoded = base64.b64encode(combined_audio).decode()
            await self.cache.set(
                "synthesis",
                encoded,
                ttl=86400,
                text_hash=cache_key,
            )
            logger.info(f"Synthesis completed: {len(combined_audio)} bytes")
            return combined_audio

        except httpx.TimeoutException as e:
            logger.error(f"Synthesis timeout after {self.settings.SARVAM_TIMEOUT}s")
            raise SynthesisException(f"Synthesis timeout: {e}")
        except httpx.HTTPStatusError as e:
            logger.error(f"Synthesis HTTP error: {e.status_code}")
            raise SynthesisException(f"Synthesis service error: {e.response.text}")
        except Exception as e:
            logger.error(f"Synthesis error: {e}")
            raise SynthesisException(f"Synthesis failed: {e}")

    async def close(self) -> None:
        logger.info("Closing speech service")
