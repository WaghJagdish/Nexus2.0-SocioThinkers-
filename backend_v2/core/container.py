from typing import Any, Callable, Dict, Optional, Type, TypeVar
from abc import ABC, abstractmethod
import asyncio

from core.config import get_settings
from core.logging import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


class Container:
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, Callable] = {}
        self._singletons: Dict[str, Any] = {}
        self._lock = asyncio.Lock()

    def register_singleton(self, key: str, instance: Any) -> None:
        self._singletons[key] = instance
        logger.info(f"Registered singleton: {key}")

    def register_factory(self, key: str, factory: Callable) -> None:
        self._factories[key] = factory
        logger.info(f"Registered factory: {key}")

    def register_service(self, key: str, service: Any) -> None:
        self._services[key] = service
        logger.info(f"Registered service: {key}")

    async def get(self, key: str) -> Any:
        if key in self._singletons:
            return self._singletons[key]

        if key in self._factories:
            return await self._factories[key]()

        if key in self._services:
            return self._services[key]

        raise KeyError(f"Service '{key}' not found in container")

    async def dispose(self) -> None:
        for key, instance in self._singletons.items():
            if hasattr(instance, "close"):
                await instance.close() if asyncio.iscoroutinefunction(instance.close) else instance.close()
                logger.info(f"Closed singleton: {key}")


_container: Optional[Container] = None


def get_container() -> Container:
    global _container
    if _container is None:
        _container = Container()
    return _container


async def setup_container() -> Container:
    from services.llm_service import LLMService
    from services.database_service import DatabaseService
    from services.cache_service import CacheService
    from services.speech_service import SpeechService
    from services.weather_service import WeatherService, GISService
    from services.scheme_service import SchemeService
    from services.eligibility_engine import HybridEligibilityEngine
    from services.retrieval_service import SchemeRetriever
    from services.form_filler import PDFFormFiller
    from repositories.farmer_repository import FarmerRepository
    from repositories.interaction_repository import InteractionRepository
    from repositories.scheme_repository import SchemeRepository
    from agents.crop_agent import CropSowingAgent
    from agents.scheme_agent import SchemeNavigatorAgent
    from pipeline.orchestration import SchemeOrchestrator

    container = get_container()
    settings = get_settings()

    logger.info("Setting up dependency injection container...")

    llm_service = LLMService(settings)
    container.register_singleton("llm_service", llm_service)

    cache_service = await CacheService.create(settings)
    container.register_singleton("cache_service", cache_service)

    database_service = await DatabaseService.create(settings)
    container.register_singleton("database_service", database_service)

    speech_service = SpeechService(settings, cache_service)
    container.register_singleton("speech_service", speech_service)

    weather_service = WeatherService(settings, cache_service)
    container.register_singleton("weather_service", weather_service)

    gis_service = GISService(settings, cache_service, llm_service)
    container.register_singleton("gis_service", gis_service)

    farmer_repo = FarmerRepository(database_service)
    container.register_singleton("farmer_repository", farmer_repo)

    interaction_repo = InteractionRepository(database_service)
    container.register_singleton("interaction_repository", interaction_repo)

    scheme_repo = SchemeRepository(database_service)
    container.register_singleton("scheme_repository", scheme_repo)

    scheme_service = SchemeService(llm_service, cache_service, repo=scheme_repo)
    container.register_singleton("scheme_service", scheme_service)

    # New services: eligibility engine, retrieval, form filler
    eligibility_engine = HybridEligibilityEngine(llm_service)
    container.register_singleton("eligibility_engine", eligibility_engine)

    retriever = SchemeRetriever(llm_service, database_service, cache_service)
    container.register_singleton("scheme_retriever", retriever)

    form_filler = PDFFormFiller()
    container.register_singleton("form_filler", form_filler)

    crop_agent = CropSowingAgent(
        llm_service,
        weather_service,
        gis_service,
    )
    container.register_singleton("crop_agent", crop_agent)

    scheme_agent = SchemeNavigatorAgent(
        llm_service,
        scheme_service,
        farmer_repo,
        eligibility_engine=eligibility_engine,
        form_filler=form_filler,
    )
    container.register_singleton("scheme_agent", scheme_agent)

    # Orchestrator: ties STT -> Graph -> TTS -> PDF pipeline
    scheme_orchestrator = SchemeOrchestrator(
        voice_service=speech_service,
        retriever=retriever,
        scheme_agent=scheme_agent,
        form_filler=form_filler,
    )
    container.register_singleton("scheme_orchestrator", scheme_orchestrator)

    logger.info("Dependency injection container setup complete")
    return container
