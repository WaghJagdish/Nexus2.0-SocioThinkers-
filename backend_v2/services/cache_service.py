from abc import ABC, abstractmethod
from typing import Any, Optional, Dict
import json
import hashlib
from datetime import datetime, timedelta
import pickle

from core.config import Settings, CacheBackend
from core.logging import get_logger

logger = get_logger(__name__)

try:
    import aioredis
except (ImportError, TypeError):
    aioredis = None


class CacheBackendBase(ABC):
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        pass

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int) -> None:
        pass

    @abstractmethod
    async def delete(self, key: str) -> None:
        pass

    @abstractmethod
    async def clear(self) -> None:
        pass

    @abstractmethod
    async def close(self) -> None:
        pass


class RedisCache(CacheBackendBase):
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.redis: Optional[aioredis.Redis] = None

    async def connect(self) -> None:
        self.redis = await aioredis.from_url(self.redis_url)
        logger.info("Connected to Redis cache")

    async def get(self, key: str) -> Optional[Any]:
        if not self.redis:
            return None
        try:
            value = await self.redis.get(key)
            if value is None:
                return None
            return pickle.loads(value)
        except Exception as e:
            logger.warning(f"Redis get error: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: int) -> None:
        if not self.redis:
            return
        try:
            await self.redis.setex(key, ttl, pickle.dumps(value))
        except Exception as e:
            logger.warning(f"Redis set error: {e}")

    async def delete(self, key: str) -> None:
        if not self.redis:
            return
        try:
            await self.redis.delete(key)
        except Exception as e:
            logger.warning(f"Redis delete error: {e}")

    async def clear(self) -> None:
        if not self.redis:
            return
        try:
            await self.redis.flushdb()
        except Exception as e:
            logger.warning(f"Redis flush error: {e}")

    async def close(self) -> None:
        if self.redis:
            await self.redis.close()
            logger.info("Closed Redis connection")


class MemoryCache(CacheBackendBase):
    def __init__(self, max_size: int = 1000):
        self.cache: Dict[str, tuple[Any, datetime]] = {}
        self.max_size = max_size

    async def get(self, key: str) -> Optional[Any]:
        if key not in self.cache:
            return None
        value, expiry = self.cache[key]
        if datetime.utcnow() > expiry:
            del self.cache[key]
            return None
        return value

    async def set(self, key: str, value: Any, ttl: int) -> None:
        if len(self.cache) >= self.max_size:
            self.cache.pop(next(iter(self.cache)))
        expiry = datetime.utcnow() + timedelta(seconds=ttl)
        self.cache[key] = (value, expiry)

    async def delete(self, key: str) -> None:
        self.cache.pop(key, None)

    async def clear(self) -> None:
        self.cache.clear()

    async def close(self) -> None:
        await self.clear()
        logger.info("Closed memory cache")


class CacheService:
    def __init__(self, backend: CacheBackendBase):
        self.backend = backend

    @staticmethod
    async def create(settings: Settings) -> "CacheService":
        cache_backend = settings.CACHE_BACKEND
        # Use memory cache as fallback if Redis is selected but aioredis is not available
        if cache_backend == CacheBackend.REDIS and aioredis is not None:
            try:
                redis_cache = RedisCache(settings.REDIS_URL)
                await redis_cache.connect()
                return CacheService(redis_cache)
            except Exception as e:
                logger.warning(f"Failed to connect to Redis, falling back to memory cache: {e}")
                return CacheService(MemoryCache())
        else:
            logger.info("Using memory cache backend")
            return CacheService(MemoryCache())

    def _make_key(self, namespace: str, **kwargs) -> str:
        key_parts = [namespace] + [f"{k}={v}" for k, v in sorted(kwargs.items())]
        key_str = "|".join(str(p) for p in key_parts)
        return hashlib.sha256(key_str.encode()).hexdigest()[:32]

    async def get(self, namespace: str, **kwargs) -> Optional[Any]:
        key = self._make_key(namespace, **kwargs)
        return await self.backend.get(key)

    async def set(self, namespace: str, value: Any, ttl: Optional[int] = None, **kwargs) -> None:
        key = self._make_key(namespace, **kwargs)
        ttl = ttl or 3600
        await self.backend.set(key, value, ttl)

    async def delete(self, namespace: str, **kwargs) -> None:
        key = self._make_key(namespace, **kwargs)
        await self.backend.delete(key)

    async def clear(self) -> None:
        await self.backend.clear()

    async def close(self) -> None:
        await self.backend.close()
        logger.info("Closed cache service")
