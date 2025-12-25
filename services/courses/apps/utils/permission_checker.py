import logging
from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied
from apps.utils.services import UserService


logger = logging.getLogger(__name__)


class IsAuthenticated(BasePermission):
    """Проверяет наличие токена и действительность пользователя."""

    def has_permission(self, request, view):
        token = request.headers.get("Authorization")
        if not token:
            return False

        token = token.replace("Bearer ", "")

        user_data = UserService.get_user_from_token(token)
        if not user_data:
            return False

        request.user_data = user_data
        return True


class IsMentor(BasePermission):
    """Проверяет, что пользователь является ментором."""

    def has_permission(self, request, view):
        if not IsAuthenticated().has_permission(request, view):
            raise PermissionDenied("Authentication required")

        user = request.user_data
        role = user.get("role")
        role_name = role.get("name")

        return role_name in ["mentor", "admin"]


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
