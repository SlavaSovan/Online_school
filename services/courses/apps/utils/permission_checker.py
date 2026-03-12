import logging
from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied
from django.core.cache import cache
from apps.utils.services import UserService


logger = logging.getLogger(__name__)


class IsAuthenticated(BasePermission):
    """Проверяет наличие токена и действительность пользователя."""

    AUTH_CACHE_TIMEOUT = 60  # 1 минута

    def _get_auth_cache_key(self, token: str) -> str:
        """Ключ для кэширования проверки авторизации"""
        import hashlib

        token_hash = hashlib.sha256(token.encode()).hexdigest()[:16]
        return f"tokens:auth_check_{token_hash}"

    def has_permission(self, request, view):
        token = request.headers.get("Authorization")
        if not token:
            return False

        token = token.replace("Bearer ", "")

        auth_cache_key = self._get_auth_cache_key(token)
        cached_auth = cache.get(auth_cache_key)

        if cached_auth is not None:
            if cached_auth is False:
                return False
            request.user_data = cached_auth
            return True

        user_data = UserService.get_user_from_token(token)

        if not user_data:
            cache.set(auth_cache_key, False, 30)  # 30 секунд
            return False

        cache.set(auth_cache_key, user_data, self.AUTH_CACHE_TIMEOUT)

        request.user_data = user_data
        return True


class IsMentor(BasePermission):
    """Проверяет, что пользователь является ментором."""

    ROLE_CACHE_TIMEOUT = 300

    def _get_role_cache_key(self, user_id: str, role_type: str) -> str:
        """Ключ для кэширования проверки ролей"""
        return f"roles:role_check_{user_id}_{role_type}"

    def has_permission(self, request, view):
        if not IsAuthenticated().has_permission(request, view):
            raise PermissionDenied("Authentication required")

        user = request.user_data
        user_id = user.get("id")
        role = user.get("role")
        role_name = role.get("name")

        cache_key = self._get_role_cache_key(user_id, "mentor")
        cached_role_check = cache.get(cache_key)

        if cached_role_check is not None:
            if cached_role_check is False:
                raise PermissionDenied("Mentor role required")
            return True

        is_mentor = role_name in ["mentor", "admin"]

        cache.set(cache_key, is_mentor, self.ROLE_CACHE_TIMEOUT)

        if not is_mentor:
            raise PermissionDenied("Mentor role required")

        return True


class IsAdmin(BasePermission):
    """Проверяет, что пользователь администратор."""

    def has_permission(self, request, view):
        if not IsAuthenticated().has_permission(request, view):
            raise PermissionDenied("Authentication required")

        user = request.user_data
        role = user.get("role")

        if role["name"] == "admin":
            return True

        raise PermissionDenied("Admin role required")
