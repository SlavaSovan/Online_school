from fastapi import Request, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Any, Dict, Optional
import logging
from app.utils.services import UserService

logger = logging.getLogger(__name__)


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    ),
) -> Dict[str, Any]:
    """Извлекает пользователя из токена."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token not provided",
        )

    token = credentials.credentials
    user_data = await UserService.get_user_from_token(token)

    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
        )

    request.state.user_data = user_data
    request.state.token = token

    return user_data


class IsAuthenticated:
    """Проверяет наличие токена и действительность пользователя."""

    async def __call__(
        self,
        request: Request,
        user: Dict[str, Any] = Depends(get_current_user),
    ) -> dict:
        return user


class IsMentor:
    """Проверяет, что пользователь является ментором."""

    async def __call__(
        self,
        request: Request,
        user: Dict[str, Any] = Depends(get_current_user),
    ) -> dict:
        role = user.get("role", {})
        role_name = role.get("name", "")

        is_mentor = role_name in ["mentor", "admin"]

        if not is_mentor:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Mentor or administrator role required",
            )

        return user


class IsAdmin:
    """Проверяет, что пользователь администратор."""

    async def __call__(
        self,
        request: Request,
        user: Dict[str, Any] = Depends(get_current_user),
    ) -> dict:
        role = user.get("role", {})
        role_name = role.get("name", "")

        if role_name != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required"
            )

        return user
