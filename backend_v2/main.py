import asyncio
import time
import uuid
from collections import defaultdict
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from core.logging import get_logger
from core.config import get_settings
from core.exceptions import ApplicationException, ErrorResponse
from core.container import setup_container, get_container
from api.routes import router
from pipeline.endpoints import router as scheme_router
from pipeline.crop_endpoints import router as crop_router

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logger.info(f"Starting Nexus API v2.0 ({settings.APP_ENV})")

    await setup_container()
    container = get_container()
    logger.info("Dependency container initialized")

    db_service = await container.get("database_service")
    if await db_service.health_check():
        logger.info("Database connection verified")
    else:
        logger.warning("Database health check failed")

    yield

    logger.info("Shutting down Nexus API")
    await container.dispose()


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Nexus Agricultural Advisory API",
        description="Multi-agent system for crop recommendations and scheme navigation",
        version="2.0.0",
        lifespan=lifespan,
    )

    origins = settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else ["*"]
    allow_creds = settings.CORS_CREDENTIALS if origins != ["*"] else False
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=allow_creds,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- In-memory rate limiter ---
    _rate_buckets: dict[str, list[float]] = defaultdict(list)

    @app.middleware("http")
    async def rate_limit_middleware(request: Request, call_next):
        if settings.ENABLE_RATE_LIMIT and request.url.path.startswith("/api/"):
            client_ip = request.client.host if request.client else "unknown"
            now = time.time()
            window = settings.RATE_LIMIT_PERIOD
            bucket = _rate_buckets[client_ip]
            # Prune expired entries
            _rate_buckets[client_ip] = bucket = [t for t in bucket if now - t < window]
            if len(bucket) >= settings.RATE_LIMIT_REQUESTS:
                return JSONResponse(
                    status_code=429,
                    content={"error_code": "RATE_LIMIT_EXCEEDED", "message": "Too many requests"},
                )
            bucket.append(now)
        return await call_next(request)

    @app.middleware("http")
    async def add_request_context(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", "")
        if not request_id:
            request_id = str(uuid.uuid4())

        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

    @app.exception_handler(ApplicationException)
    async def application_exception_handler(request: Request, exc: ApplicationException):
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                code=exc.error_code,
                message=exc.message,
                details=exc.details,
                status_code=exc.status_code,
                request_id=getattr(request.state, "request_id", "unknown"),
            ).to_dict(),
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error_code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
                "status_code": 500,
                "request_id": getattr(request.state, "request_id", "unknown"),
            },
        )

    app.include_router(router)
    app.include_router(scheme_router)
    app.include_router(crop_router)

    @app.get("/")
    async def root():
        return {
            "service": "Nexus Agricultural Advisory",
            "version": "2.0.0",
            "status": "running",
        }

    return app

app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()

    app = create_app()

    uvicorn.run(
        app,
        host=settings.HOST,
        port=settings.PORT,
        log_level=settings.LOG_LEVEL.value.lower(),
        reload=settings.is_development,
    )
