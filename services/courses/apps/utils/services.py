import httpx
import logging
from django.conf import settings
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class UserService:
    """Сервис для взаимодействия с User Service"""

    _client: Optional[httpx.Client] = None

    @classmethod
    def _get_client(cls) -> httpx.Client:
        """Получение HTTP клиента с пулом соединений"""
        if cls._client is None:
            cls._client = httpx.Client(
                timeout=5.0,
                limits=httpx.Limits(max_keepalive_connections=10, max_connections=100),
            )
        return cls._client

    @classmethod
    def get_user_from_token(cls, token: str) -> Optional[Dict[str, Any]]:
        """Получение информации о пользователе по токену"""
        if not token:
            return None

        try:
            client = cls._get_client()

            headers = {"Authorization": f"Bearer {token}"}
            response = client.get(
                f"{settings.USER_SERVICE_URL}/auth/profile",
                headers=headers,
            )

            if response.status_code == 200:
                return response.json()

            return None

        except httpx.TimeoutException:
            logger.warning(f"User service timeout for token: {token[:20]}...")
            return None
        except httpx.RequestError as e:
            logger.error(f"Failed to get user from token: {e}")
            return None
