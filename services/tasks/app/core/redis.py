import json
import logging
import redis.asyncio as redis
from typing import Any, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)


class RedisClient:
    _client: Optional[redis.Redis] = None

    @classmethod
    async def get_client(cls) -> redis.Redis:
        if cls._client is None:
            try:
                cls._client = redis.from_url(
                    settings.REDIS.redis_url,
                    decode_responses=True,
                    socket_timeout=5,
                    socket_connect_timeout=5,
                    retry_on_timeout=True,
                )
                await cls._client.ping()
                logger.info("Redis connection established")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                cls._client = None
        return cls._client

    @classmethod
    def close(cls):
        """Закрытие соединения с Redis"""
        if cls._client:
            cls._client.close()
            cls._client = None


class RedisCacheClient:
    _client: Optional[redis.Redis] = None
    _prefix: str = "tasks_ms:"

    @classmethod
    async def _get_client(cls) -> redis.Redis:
        if cls._client is None:
            try:
                cls._client = redis.from_url(
                    settings.REDIS.redis_cache_url,
                    decode_responses=True,
                    socket_timeout=5,
                    socket_connect_timeout=5,
                    retry_on_timeout=True,
                )
                await cls._client.ping()
                logger.info("Redis connection established")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                cls._client = None
        return cls._client

    @classmethod
    async def close(cls):
        """Закрытие соединения"""
        if cls._client:
            await cls._client.close()
            cls._client = None

    @classmethod
    async def set(cls, key: str, value: Any, ttl_seconds: int = 300):
        """Сохранение в кэш"""
        try:
            client = await cls._get_client()
            if client:
                await client.setex(
                    f"{cls._prefix}{key}",
                    ttl_seconds,
                    json.dumps(value, default=str),
                )

        except Exception as e:
            logger.warning(f"Cache set error: {e}")

    @classmethod
    async def get(cls, key: str) -> Optional[Any]:
        """Получение из кэша"""
        try:
            client = await cls._get_client()
            if client:
                value = await client.get(f"{cls._prefix}{key}")
                if value:
                    return json.loads(value)

        except Exception as e:
            logger.warning(f"Cache get error: {e}")
        return None

    @classmethod
    async def delete(cls, key: str):
        """Удаление из кэша"""
        try:
            client = await cls._get_client()
            if client:
                await client.delete(f"{cls._prefix}{key}")
        except Exception as e:
            logger.error(f"Cache delete error: {e}")

    @classmethod
    async def delete_pattern(cls, pattern: str):
        """Удаление из кэша по паттерну"""
        try:
            client = await cls._get_client()
            if client:
                keys = await client.keys(f"{cls._prefix}{pattern}")
                if keys:
                    await client.delete(*keys)
        except Exception as e:
            logger.error(f"Cache delete_pattern error: {e}")
