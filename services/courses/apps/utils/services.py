import requests
import logging
from django.conf import settings
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class UserService:
    """Сервис для взаимодействия с User Service"""

    @staticmethod
    def get_user_from_token(token: str) -> Optional[Dict[str, Any]]:
        """Получение информации о пользователе по токену"""
        try:
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(
                f"{settings.USER_SERVICE_URL}/auth/profile",
                headers=headers,
                timeout=10,
            )
            if response.status_code == 200:
                return response.json()
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get user from token: {e}")
            return None
