from typing import AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.users.models import User
from app.users.services import PermissionService, RoleService, UserService
from app.users.permissions import (
    can_edit_own_profile,
    can_read_any_profile,
    can_manage_users,
    can_manage_roles,
    can_manage_permissions,
)


async def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    return UserService(db)


async def get_role_service(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(can_manage_roles),
) -> RoleService:
    return RoleService(db)


async def get_permission_service(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(can_manage_permissions),
) -> PermissionService:
    return PermissionService(db)


async def get_user_service_for_edit(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(can_edit_own_profile),
) -> UserService:
    return UserService(db)


async def get_user_service_for_any_read(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(can_read_any_profile),
) -> UserService:
    return UserService(db)


async def get_user_service_for_manage(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(can_manage_users),
) -> UserService:
    return UserService(db)
