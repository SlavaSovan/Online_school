import hashlib
import requests
import logging
from django.conf import settings
from django.core.cache import cache
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class UserService:
    """Сервис для взаимодействия с User Service"""

    TOKEN_CACHE_TIMEOUT = 300  # 5 минут
    USER_CACHE_TIMEOUT = 600  # 10 минут

    @staticmethod
    def _get_token_cache_key(token: str) -> str:
        """Генерирует ключ для кэширования токена"""
        token_hash = hashlib.sha256(token.encode()).hexdigest()[:16]
        return f"tokens:user_token_{token_hash}"

    @staticmethod
    def _get_user_cache_key(user_id: str) -> str:
        """Генерирует ключ для кэширования пользователя"""
        return f"users:user_data_{user_id}"

    @staticmethod
    def get_user_from_token(token: str) -> Optional[Dict[str, Any]]:
        """Получение информации о пользователе по токену"""
        if not token:
            return None

        cache_key = UserService._get_token_cache_key(token)
        cached_user = cache.get(cache_key)

        if cached_user is not None:
            if settings.DEBUG:
                logger.debug(f"Token cache HIT for key: {cache_key[:20]}...")
            return cached_user

        if settings.DEBUG:
            logger.debug(f"Token cache MISS for key: {cache_key[:20]}...")

        try:
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(
                f"{settings.USER_SERVICE_URL}/auth/profile",
                headers=headers,
                timeout=5,
            )
            if response.status_code == 200:
                user_data = response.json()
                cache.set(cache_key, user_data, UserService.TOKEN_CACHE_TIMEOUT)
                user_id = user_data.get("id")

                if user_id:
                    user_cache_key = UserService._get_user_cache_key(user_id)
                    cache.set(user_cache_key, user_data, UserService.USER_CACHE_TIMEOUT)

                return user_data

            if response.status_code in [401, 403]:  # Неавторизован/запрещено
                cache.set(cache_key, None, 60)  # 1 минута

            return None
        except requests.exceptions.Timeout:
            logger.warning(f"User service timeout for token: {token[:20]}...")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get user from token: {e}")
            return None

    @staticmethod
    def invalidate_user_cache(token: str = None, user_id: str = None):
        """Инвалидация кэша пользователя"""
        if token:
            cache_key = UserService._get_token_cache_key(token)
            cache.delete(cache_key)

        if user_id:
            cache_key = UserService._get_user_cache_key(user_id)
            cache.delete(cache_key)
