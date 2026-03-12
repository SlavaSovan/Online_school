from fastapi import Depends, HTTPException, status

from app.auth.validation import get_current_active_user_with_permissions
from .models import User


class PermissionChecker:
    def __init__(self, permission_name: str):
        self.permission_name = permission_name

    async def __call__(
        self, user: User = Depends(get_current_active_user_with_permissions)
    ):

        permission_names = {p.name for p in user.role.permissions}
        has_specific_permission = self.permission_name in permission_names

        required_admin_permissions = {
            "role:write",
            "permission:write",
            "user:write:any",
        }
        is_admin_by_role = user.role.name.lower() == "admin"
        has_all_admin_permissions = required_admin_permissions.issubset(
            user.role.permissions
        )
        is_admin = is_admin_by_role and has_all_admin_permissions

        if has_specific_permission or is_admin:
            return user

        if self.permission_name.startswith("user:"):
            if "own" in self.permission_name:
                message = "You can only access your own data"
            elif "any" in self.permission_name:
                message = "You don't have permission to access user data"
            else:
                message = "Access denied"

        elif self.permission_name.startswith("role:"):
            if "read" in self.permission_name:
                message = "You don't have permission to view roles"
            else:
                message = "You don't have permission to manage roles"

        elif self.permission_name.startswith("permission:"):
            if "read" in self.permission_name:
                message = "You don't have permission to view permissions"
            else:
                message = "You don't have permission to manage permissions"

        else:
            message = "You don't have permission to perform this action"

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=message,
        )


can_read_own_profile = PermissionChecker("user:read:own")
can_edit_own_profile = PermissionChecker("user:write:own")
can_read_any_profile = PermissionChecker("user:read:any")
can_manage_roles = PermissionChecker("role:write")
can_manage_permissions = PermissionChecker("permission:write")
can_manage_users = PermissionChecker("user:write:any")
