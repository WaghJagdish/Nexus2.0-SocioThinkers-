from typing import Optional, Dict, Any
import asyncio
from functools import lru_cache

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.messages import BaseMessage
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
import httpx

from core.config import Settings
from core.logging import get_logger
from core.exceptions import ExternalServiceException, TimeoutException

logger = get_logger(__name__)


class LLMService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._llm: Optional[ChatOpenAI] = None
        self._embeddings: Optional[OpenAIEmbeddings] = None

    @property
    def llm(self) -> ChatOpenAI:
        if self._llm is None:
            self._llm = ChatOpenAI(
                model=self.settings.LLM_MODEL,
                api_key=self.settings.OPENAI_API_KEY,
                base_url=self.settings.LLM_BASE_URL,
                temperature=self.settings.LLM_TEMPERATURE,
                max_tokens=self.settings.LLM_MAX_TOKENS,
                timeout=self.settings.LLM_TIMEOUT,
            )
        return self._llm

    @property
    def embeddings(self) -> OpenAIEmbeddings:
        if self._embeddings is None:
            self._embeddings = OpenAIEmbeddings(
                model=self.settings.EMBEDDING_MODEL,
                api_key=self.settings.OPENAI_API_KEY,
                base_url=self.settings.LLM_BASE_URL,
            )
        return self._embeddings

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.HTTPError, TimeoutError)),
    )
    async def invoke(
        self,
        messages: list[BaseMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        try:
            response = await asyncio.wait_for(
                self.llm.ainvoke(
                    messages,
                    config={
                        "temperature": temperature or self.settings.LLM_TEMPERATURE,
                        "max_tokens": max_tokens or self.settings.LLM_MAX_TOKENS,
                    },
                ),
                timeout=self.settings.LLM_TIMEOUT,
            )
            return response.content
        except asyncio.TimeoutError:
            logger.error(f"LLM invocation timed out after {self.settings.LLM_TIMEOUT}s")
            raise TimeoutException("LLM inference", self.settings.LLM_TIMEOUT)
        except Exception as e:
            logger.error(f"LLM invocation failed: {e}")
            raise ExternalServiceException("LLM", str(e))

    async def invoke_structured(
        self,
        messages: list[BaseMessage],
        response_schema: type,
        temperature: Optional[float] = None,
    ) -> Any:
        try:
            llm_with_schema = self.llm.with_structured_output(response_schema)
            response = await asyncio.wait_for(
                llm_with_schema.ainvoke(
                    messages,
                    config={"temperature": temperature or self.settings.LLM_TEMPERATURE},
                ),
                timeout=self.settings.LLM_TIMEOUT,
            )
            return response
        except asyncio.TimeoutError:
            logger.error(f"Structured LLM invocation timed out")
            raise TimeoutException("LLM structured inference", self.settings.LLM_TIMEOUT)
        except Exception as e:
            logger.error(f"Structured LLM invocation failed: {e}")
            raise ExternalServiceException("LLM", str(e))

    async def embed_text(self, text: str) -> list[float]:
        try:
            embedding = await asyncio.wait_for(
                self.embeddings.aembed_query(text),
                timeout=self.settings.LLM_TIMEOUT,
            )
            return embedding
        except asyncio.TimeoutError:
            logger.error(f"Embedding timed out")
            raise TimeoutException("Text embedding", self.settings.LLM_TIMEOUT)
        except Exception as e:
            logger.error(f"Embedding failed: {e}")
            raise ExternalServiceException("Embedding", str(e))

    async def close(self) -> None:
        logger.info("Closing LLM service")
