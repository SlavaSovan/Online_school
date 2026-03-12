import redis.asyncio as redis
from typing import Optional
from datetime import datetime, timedelta
import json
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class TokenBlacklist:
    """Класс для управления черным списком токенов через Redis"""

    def __init__(self):
        self.redis_client = None
        self.redis_host = settings.REDIS.REDIS_HOST
        self.redis_port = settings.REDIS.REDIS_PORT

    async def connect(self):
        if not self.redis_client:
            try:
                self.redis_client = await redis.from_url(
                    f"redis://{self.redis_host}:{self.redis_port}/0",
                    decode_responses=True,
                )
                await self.redis_client.ping()
                logger.info("Connected to Redis")
            except Exception as e:
                logger.error(f"Redis connection failed: {e}")
                self.redis_client = None

    async def close(self):
        if self.redis_client:
            await self.redis_client.close()
            self.redis_client = None

    async def add_to_blacklist(self, token: str, expires_in: int) -> bool:
        if not self.redis_client:
            await self.connect()

        if not self.redis_client:
            logger.error("Redis not available")
            return False

        try:
            await self.redis_client.setex(f"blacklist:{token}", expires_in, "revoked")
            logger.info(f"Token added to blacklist (expires in {expires_in}s)")
            return True
        except Exception as e:
            logger.error(f"Failed to add token to blacklist: {e}")
            return False

    async def is_blacklisted(self, token: str) -> bool:
        if not self.redis_client:
            await self.connect()
        if not self.redis_client:
            return False
        try:
            return await self.redis_client.exists(f"blacklist:{token}") > 0
        except Exception as e:
            logger.error(f"Failed to check blacklist: {e}")
            return False


token_blacklist = TokenBlacklist()


async def get_token_blacklist() -> TokenBlacklist:
    await token_blacklist.connect()
    return token_blacklist
