from fastapi import Depends, HTTPException, status

from app.auth.validation import get_current_active_user_with_permissions
from .models import User


class PermissionChecker:
    def __init__(self, permission_name: str):
        self.permission_name = permission_name

    async def __call__(
        self, user: User = Depends(get_current_active_user_with_permissions)
    ):

        has_permission = any(
            perm.name == self.permission_name for perm in user.role.permissions
        )

        if not has_permission:
            has_admin_permission = any(
                perm.name == "role:write" for perm in user.role.permissions
            )

            if not has_admin_permission and user.role.name.lower() != "admin":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission '{self.permission_name}' or 'role:write' required",
                )
        return user


can_read_own_profile = PermissionChecker("user:read:own")
can_edit_own_profile = PermissionChecker("user:write:own")
can_read_any_profile = PermissionChecker("user:read:any")
can_edit_any_profile = PermissionChecker("user:write:any")
can_manage_roles = PermissionChecker("role:write")
can_manage_permissions = PermissionChecker("permission:write")
can_manage_users = PermissionChecker("user:write:any")
