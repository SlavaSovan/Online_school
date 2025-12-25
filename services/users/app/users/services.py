from typing import List
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.utils import hash_password, validate_password

from app.users.repository import PermissionRepository, RoleRepository, UserRepository
from app.users.schemas import (
    PasswordChange,
    PermissionCreate,
    PermissionResponse,
    PermissionUpdate,
    RoleCreate,
    RoleDetailResponse,
    RoleResponse,
    RoleUpdate,
    UserCreate,
    UserDetailResponse,
    UserListResponse,
    UserResponse,
    UserUpdate,
)


class PermissionService:
    def __init__(self, db: AsyncSession):
        self.repository = PermissionRepository(db)

    async def get_all_permissions(self) -> List[PermissionResponse]:
        permissions = await self.repository.get_all()
        return [PermissionResponse.model_validate(p) for p in permissions]

    async def get_permissions_by_category(
        self, category: str
    ) -> List[PermissionResponse]:
        permissions = await self.repository.get_by_category(category)
        return [PermissionResponse.model_validate(p) for p in permissions]

    async def get_permission_by_id(self, permission_id: int) -> PermissionResponse:
        permission = await self.repository.get_by_id(permission_id)
        if not permission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Permission with id {permission_id} not found",
            )
        return PermissionResponse.model_validate(permission)

    async def get_permission_by_name(self, name: str) -> PermissionResponse:
        permission = await self.repository.get_by_name(name)
        if not permission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Permission with name '{name}' not found",
            )
        return PermissionResponse.model_validate(permission)

    async def create_permission(
        self, permission_data: PermissionCreate
    ) -> PermissionResponse:
        existing_permission = await self.repository.get_by_name(permission_data.name)
        if existing_permission:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Permission with name '{permission_data.name}' already exists",
            )

        permission = await self.repository.create(permission_data)
        return PermissionResponse.model_validate(permission)

    async def update_permission(
        self, permission_id: int, permission_data: PermissionUpdate
    ) -> PermissionResponse:
        permission = await self.repository.get_by_id(permission_id)
        if not permission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Permission with id {permission_id} not found",
            )

        permission = await self.repository.update(permission_id, permission_data)
        return PermissionResponse.model_validate(permission)

    async def delete_permission(self, permission_id: int) -> bool:
        permission = await self.repository.get_by_id(permission_id)
        if not permission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Permission with id {permission_id} not found",
            )

        has_dependecies = await self.repository.has_role_dependencies(permission_id)
        if has_dependecies:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete permission. It is used by role(s). "
                f"Remove permission from roles first.",
            )

        deleted = await self.repository.delete(permission_id)
        return deleted


class RoleService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = RoleRepository(db)

    async def get_all_roles(self) -> List[RoleResponse]:
        roles = await self.repository.get_all()
        role_responses = []

        for role in roles:
            user_count = await self.repository._count_users_with_role(role.id)
            role_response = RoleResponse.model_validate(role)
            role_response.user_count = user_count
            role_responses.append(role_response)

        return role_responses

    async def get_role_by_id(self, role_id: int) -> RoleDetailResponse:
        role = await self.repository.get_by_id(role_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role with id {role_id} not found",
            )

        user_count = await self.repository._count_users_with_role(role_id)
        role_response = RoleDetailResponse.model_validate(role)
        role_response.user_count = user_count
        return role_response

    async def create_role(self, role_data: RoleCreate) -> RoleResponse:
        existing_role = await self.repository.get_by_name(role_data.name)
        if existing_role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Role with name '{role_data.name}' already exists",
            )

        role = await self.repository.create(role_data)
        user_count = await self.repository._count_users_with_role(role.id)
        role_response = RoleResponse.model_validate(role)
        role_response.user_count = user_count
        return role_response

    async def update_role(self, role_id: int, role_data: RoleUpdate) -> RoleResponse:
        existing_role = await self.repository.get_by_id(role_id)
        if not existing_role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role with id {role_id} not found",
            )

        if role_data.name and role_data.name != existing_role.name:
            role_with_same_name = await self.repository.get_by_name(role_data.name)
            if role_with_same_name and role_with_same_name.id != role_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Role with name '{role_data.name}' already exists",
                )

        role = await self.repository.update(role_id, role_data)
        user_count = await self.repository._count_users_with_role(role_id)
        role_response = RoleResponse.model_validate(role)
        role_response.user_count = user_count
        return role_response

    async def delete_role(self, role_id: int) -> bool:
        try:
            return await self.repository.delete(role_id)
        except ValueError as e:
            if "Cannot delete default role" in str(e):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e),
                )
            elif "Cannot delete role with" in str(e):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e),
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=str(e),
                )

    async def set_default_role(self, role_id: int) -> RoleResponse:
        try:
            role = await self.repository.set_default_role(role_id)
            user_count = await self.repository._count_users_with_role(role_id)
            role_response = RoleResponse.model_validate(role)
            role_response.user_count = user_count
            return role_response
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            )

    async def update_role_permissions(
        self, role_id: int, permission_ids: List[int]
    ) -> RoleResponse:
        role = await self.repository.set_role_permissions(role_id, permission_ids)
        role_detail = await self.repository.get_by_id(role.id)
        return RoleResponse.model_validate(role_detail)

    async def add_permission_to_role(
        self, role_id: int, permission_id: int
    ) -> RoleDetailResponse:
        role = await self.repository.add_permission_to_role(role_id, permission_id)
        role_detail = await self.repository.get_by_id(role.id)
        return RoleDetailResponse.model_validate(role_detail)

    async def remove_permission_from_role(
        self, role_id: int, permission_id: int
    ) -> RoleResponse:
        role = await self.repository.remove_permission_from_role(role_id, permission_id)
        role_detail = await self.repository.get_by_id(role.id)
        return RoleResponse.model_validate(role_detail)


class UserService:
    def __init__(self, db: AsyncSession):
        self.repository = UserRepository(db)
        self.role_repository = RoleRepository(db)

    async def get_all_users(self) -> UserListResponse:
        users = await self.repository.get_all()
        users_response = [UserResponse.model_validate(u) for u in users]
        return UserListResponse(users=users_response, total=len(users_response))

    async def get_user_by_id(self, user_id: int) -> UserDetailResponse:
        user = await self.repository.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id {user_id} not found",
            )
        return UserDetailResponse.model_validate(user)

    async def get_user_by_email(self, email: str) -> UserResponse:
        user = await self.repository.get_by_email(email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User not found",
            )
        return UserDetailResponse.model_validate(user)

    async def get_users_by_role(self, role_id: int) -> UserListResponse:
        role = await self.role_repository.get_by_id(role_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role with id {role_id} not found",
            )
        users = await self.repository.get_by_role(role_id)
        users_response = [UserResponse.model_validate(u) for u in users]
        return UserListResponse(users=users_response, total=len(users_response))

    async def create_user(self, user_data: UserCreate) -> UserResponse:
        if await self.repository.is_email_taken(user_data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        if await self.repository.is_username_taken(user_data.username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered",
            )

        if user_data.password != user_data.password_confirm:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Passwords do not match",
            )

        role_id = user_data.role_id

        if role_id is None:
            default_role = await self.role_repository.get_default_role()
            if not default_role:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="No default role configured in the system.",
                )
            role_id = default_role.id
        else:
            role = await self.role_repository.get_by_id(role_id)
            if not role:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Role with id {role_id} not found",
                )

        hashed_password = hash_password(user_data.password)
        user = await self.repository.create(user_data, hashed_password, role_id)
        return UserResponse.model_validate(user)

    async def update_user(self, user_id, user_data: UserUpdate) -> UserResponse:
        user = await self.repository.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User not found",
            )

        if user_data.email and await self.repository.is_email_taken(
            user_data.email, user_id
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        if user_data.role_id is not None:
            if not await self.role_repository.get_by_id(user_data.role_id):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Role with id {user_data.role_id} not found",
                )

        updated = await self.repository.update(user_id, user_data)
        return UserResponse.model_validate(updated)

    async def change_password(self, user_id: int, data: PasswordChange) -> bool:
        user = await self.repository.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User not found",
            )

        if not validate_password(data.old_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Old password is incorrect",
            )

        if data.new_password != data.new_password_confirm:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password confirmation doesn't match",
            )

        new_hash = hash_password(data.new_password)
        await self.repository.update_password(user_id, new_hash)
        return True

    async def delete_user(self, user_id: int) -> bool:
        deleted = await self.repository.delete(user_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id {user_id} not found",
            )
        return deleted
