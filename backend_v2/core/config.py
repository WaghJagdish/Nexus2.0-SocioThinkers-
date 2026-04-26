from enum import Enum
from typing import Literal
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings
from pydantic import Field


class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class CacheBackend(str, Enum):
    REDIS = "redis"
    MEMORY = "memory"
    NONE = "none"


class Settings(BaseSettings):
    APP_ENV: Environment = Field(default=Environment.DEVELOPMENT)
    APP_NAME: str = "Kisan Setu"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False
    LOG_LEVEL: LogLevel = LogLevel.INFO

    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 4

    OPENAI_API_KEY: str = Field(default="", min_length=10)
    LLM_BASE_URL: str = "https://integrate.api.nvidia.com/v1"
    LLM_MODEL: str = "openai/gpt-oss-120b"
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    LLM_TEMPERATURE: float = 0.1
    LLM_MAX_TOKENS: int = 4096
    LLM_TIMEOUT: int = 30
    LLM_RETRIES: int = 3

    SUPABASE_URL: str = Field(default="")
    SUPABASE_KEY: str = Field(default="")
    DATABASE_URL: str = Field(default="")
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    DATABASE_ECHO: bool = False

    SARVAM_API_KEY: str = Field(default="")
    SARVAM_TIMEOUT: int = 30
    SARVAM_RETRIES: int = 3

    BHUVAN_WMS_URL: str = "https://bhuvan-vec2.nrsc.gov.in/bhuvan/wms"
    WEATHER_API_TIMEOUT: int = 15
    WEATHER_CACHE_TTL: int = 3600

    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_TIMEOUT: int = 5

    CACHE_BACKEND: CacheBackend = CacheBackend.REDIS
    CACHE_TTL_SECONDS: int = 3600

    MAX_RETRIES: int = 3
    REQUEST_TIMEOUT: int = 30
    IDEMPOTENCY_TTL: int = 86400

    CORS_ORIGINS: list[str] = ["*"]
    CORS_CREDENTIALS: bool = True
    CORS_METHODS: list[str] = ["*"]
    CORS_HEADERS: list[str] = ["*"]

    SECRET_KEY: str = Field(default="", min_length=32)
    API_KEY_HEADER: str = "X-API-Key"
    ENABLE_RATE_LIMIT: bool = True
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD: int = 60

    PROMETHEUS_ENABLED: bool = True
    SENTRY_DSN: str = ""

    GENERATED_PDFS_DIR: str = "./generated_pdfs"
    GENERATED_AUDIO_DIR: str = "./generated_audio"
    SCHEME_DATA_DIR: str = "./data/schemes"
    LOG_FILE_PATH: str = "./logs/app.log"
    MAX_LOG_SIZE: int = 104857600
    BACKUP_COUNT: int = 10

    class Config:
        env_file = Path(__file__).parent.parent / ".env"
        env_file_encoding = "utf-8"
        extra = "allow"
        case_sensitive = True

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == Environment.PRODUCTION

    @property
    def is_development(self) -> bool:
        return self.APP_ENV == Environment.DEVELOPMENT


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
