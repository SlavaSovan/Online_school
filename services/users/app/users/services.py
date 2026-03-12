from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.utils import hash_password, validate_password

from app.users.exceptions import (
    CannotDeactivateSelfError,
    CannotDeleteSelfError,
    DefaultRoleError,
    InvalidPasswordError,
    PasswordMismatchError,
    PermissionAlreadyExistsError,
    PermissionInUseError,
    PermissionNotFoundError,
    RoleAlreadyExistsError,
    RoleHasUsersError,
    RoleNotFoundError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from app.users.models import Permission, Role, User
from app.users.repository import PermissionRepository, RoleRepository, UserRepository
from app.users.schemas import (
    PasswordChange,
    PermissionCreate,
    PermissionUpdate,
    RoleCreate,
    RoleUpdate,
    UserCreate,
    UserUpdate,
)


class PermissionService:
    def __init__(self, db: AsyncSession):
        self.repository = PermissionRepository(db)

    async def get_all_permissions(self) -> List[Permission]:
        return await self.repository.get_all()

    async def get_permission_by_id(self, permission_id: int) -> Permission:
        permission = await self.repository.get_by_id(permission_id)
        if not permission:
            raise PermissionNotFoundError(permission_id=permission_id)
        return permission

    async def get_permission_by_name(self, name: str) -> Permission:
        permission = await self.repository.get_by_name(name)
        if not permission:
            raise PermissionNotFoundError(name=name)
        return permission

    async def create_permission(self, permission_data: PermissionCreate) -> Permission:
        existing = await self.repository.get_by_name(permission_data.name)
        if existing:
            raise PermissionAlreadyExistsError(name=permission_data.name)

        return await self.repository.create(permission_data.model_dump())

    async def update_permission(
        self, permission_id: int, permission_data: PermissionUpdate
    ) -> Permission:
        permission = await self.repository.get_by_id(permission_id)
        if not permission:
            raise PermissionNotFoundError(permission_id=permission_id)

        update_data = permission_data.model_dump(exclude_unset=True)
        return await self.repository.update(permission, update_data)

    async def delete_permission(self, permission_id: int) -> bool:
        permission = await self.repository.get_by_id(permission_id)
        if not permission:
            raise PermissionNotFoundError(permission_id=permission_id)

        has_dependecies = await self.repository.has_role_dependencies(permission_id)
        if has_dependecies:
            raise PermissionInUseError(permission_id=permission_id)

        return await self.repository.delete(permission)


class RoleService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = RoleRepository(db)
        self.permission_repository = PermissionRepository(db)

    async def get_all_roles(self) -> List[Tuple[Role, int]]:
        return await self.repository.get_all_with_stats()

    async def get_role_by_id(self, role_id: int) -> Tuple[Role, int, List[Permission]]:
        result = await self.repository.get_by_id_with_details(role_id)
        if not result:
            raise RoleNotFoundError(role_id=role_id)
        role, user_count, permissions = result
        return role, user_count, permissions

    async def create_role(self, role_data: RoleCreate) -> Role:
        existing = await self.repository.get_by_name(role_data.name)
        if existing:
            raise RoleAlreadyExistsError(name=role_data.name)

        role_dict = role_data.model_dump(exclude={"permission_ids"}, exclude_unset=True)

        if role_dict.get("is_default", False):
            await self.repository.reset_default_roles()

        permissions = None
        if role_data.permission_ids:
            permissions = await self.permission_repository.get_by_ids(
                role_data.permission_ids
            )

        return await self.repository.create(role_dict, permissions)

    async def update_role(self, role_id: int, role_data: RoleUpdate) -> Role:
        role = await self.repository.get_by_id(role_id)
        if not role:
            raise RoleNotFoundError(role_id=role_id)

        update_dict = role_data.model_dump(
            exclude={"permission_ids"}, exclude_unset=True
        )

        if "name" in update_dict and update_dict["name"] != role.name:
            existing = await self.repository.get_by_name(role_data.name)
            if existing and existing.id != role_id:
                raise RoleAlreadyExistsError(name=role_data.name)

        if update_dict.get("is_default", False) and not role.is_default:
            await self.repository.reset_default_roles(exclude_role_id=role_id)

        role = await self.repository.update(role, update_dict)

        if role_data.permission_ids is not None:
            permissions = await self.permission_repository.get_by_ids(
                role_data.permission_ids
            )
            role = await self.repository.set_permissions(role, permissions)

        return role

    async def delete_role(self, role_id: int) -> bool:
        role = await self.repository.get_by_id(role_id)
        if not role:
            raise RoleNotFoundError(role_id=role_id)

        if role.is_default:
            raise DefaultRoleError(action="delete")

        user_count = await self.repository.count_users_by_role(role_id)
        if user_count > 0:
            raise RoleHasUsersError(role_id=role_id, user_count=user_count)

        return await self.repository.delete(role)

    async def set_default_role(self, role_id: int) -> Role:
        role = await self.repository.get_by_id(role_id)
        if not role:
            raise RoleNotFoundError(role_id=role_id)

        await self.repository.reset_default_roles(exclude_role_id=role_id)

        if not role.is_default:
            role.is_default = True
            await self.repository.update(role, {})

        return role

    async def add_permission_to_role(self, role_id: int, permission_id: int) -> Role:
        role = await self.repository.get_by_id(role_id)
        if not role:
            raise RoleNotFoundError(role_id=role_id)
        permission = await self.permission_repository.get_by_id(permission_id)
        if not permission:
            raise PermissionNotFoundError(permission_id=permission_id)

        return await self.repository.add_permission(role, permission)

    async def remove_permission_from_role(
        self, role_id: int, permission_id: int
    ) -> Role:
        role = await self.repository.get_by_id(role_id)
        if not role:
            raise RoleNotFoundError(role_id=role_id)

        permission = await self.permission_repository.get_by_id(permission_id)
        if not permission:
            raise PermissionNotFoundError(permission_id=permission_id)

        return await self.repository.remove_permission(role, permission)

    async def update_role_permissions(
        self, role_id: int, permission_ids: List[int]
    ) -> Role:
        role = await self.repository.get_by_id(role_id)
        if not role:
            raise RoleNotFoundError(role_id=role_id)

        permissions = await self.permission_repository.get_by_ids(permission_ids)
        return await self.repository.set_permissions(role, permissions)


class UserService:
    def __init__(self, db: AsyncSession, current_user: Optional[User] = None):
        self.db = db
        self.repository = UserRepository(db)
        self.role_repository = RoleRepository(db)
        self.current_user = current_user

    async def get_all_users(
        self, skip: int = 0, limit: int = 100, include_inactive: bool = False
    ) -> Tuple[List[User], int]:
        users, total = await self.repository.get_all(
            skip=skip, limit=limit, include_inactive=include_inactive
        )
        return users, total

    async def get_user_by_id(
        self, user_id: int, include_inactive: bool = False
    ) -> User:
        user = await self.repository.get_by_id(
            user_id, include_inactive=include_inactive
        )
        if not user:
            raise UserNotFoundError(user_id=user_id)
        return user

    async def get_user_by_email(
        self, email: str, include_inactive: bool = False
    ) -> User:
        user = await self.repository.get_by_email(
            email, include_inactive=include_inactive
        )
        if not user:
            raise UserNotFoundError(email=email)
        return user

    async def get_users_by_role(
        self,
        role_id: int,
        skip: int = 0,
        limit: int = 100,
        include_inactive: bool = False,
    ) -> Tuple[List[User], int]:
        role = await self.role_repository.get_by_id(role_id)
        if not role:
            raise RoleNotFoundError(role_id=role_id)

        users, total = await self.repository.get_by_role(
            role_id,
            skip=skip,
            limit=limit,
            include_inactive=include_inactive,
        )
        return users, total

    async def create_user(self, user_data: UserCreate) -> User:
        if await self.repository.is_email_taken(user_data.email):
            raise UserAlreadyExistsError(email=user_data.email)

        if user_data.password != user_data.password_confirm:
            raise PasswordMismatchError()

        role_id = user_data.role_id
        if role_id is None:
            default_role = await self.role_repository.get_default_role()
            if not default_role:
                raise DefaultRoleError(action="assign")
            role_id = default_role.id
        else:
            role = await self.role_repository.get_by_id(role_id)
            if not role:
                raise RoleNotFoundError(role_id=role_id)

        hashed_password = hash_password(user_data.password)

        # Создание пользователя
        user = await self.repository.create(
            email=user_data.email,
            hashed_password=hashed_password,
            role_id=role_id,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            patronymic=user_data.patronymic,
        )

        return user

    async def update_user(self, user_id: int, user_data: UserUpdate) -> User:
        user = await self.repository.get_by_id(user_id, include_inactive=True)
        if not user:
            raise UserNotFoundError(user_id=user_id)

        update_data = {}

        if user_data.email is not None and user_data.email != user.email:
            if await self.repository.is_email_taken(
                user_data.email, exclude_user_id=user_id
            ):
                raise UserAlreadyExistsError(email=user_data.email)
            update_data["email"] = user_data.email

        if user_data.first_name is not None:
            update_data["first_name"] = user_data.first_name
        if user_data.last_name is not None:
            update_data["last_name"] = user_data.last_name
        if user_data.patronymic is not None:
            update_data["patronymic"] = user_data.patronymic

        if user_data.is_active is not None:
            if (
                self.current_user
                and self.current_user.id == user_id
                and user_data.is_active is False
            ):
                raise CannotDeactivateSelfError()
            update_data["is_active"] = user_data.is_active

        if user_data.role_id is not None and user_data.role_id != user.role_id:
            role = await self.role_repository.get_by_id(user_data.role_id)
            if not role:
                raise RoleNotFoundError(role_id=user_data.role_id)
            update_data["role_id"] = user_data.role_id

        if update_data:
            user = await self.repository.update(user, **update_data)

        return user

    async def change_password(
        self, user_id: int, password_data: PasswordChange
    ) -> User:
        user = await self.repository.get_by_id(user_id, include_inactive=True)
        if not user:
            raise UserNotFoundError(user_id=user_id)

        if not validate_password(password_data.old_password, user.hashed_password):
            raise InvalidPasswordError()

        if password_data.new_password != password_data.new_password_confirm:
            raise PasswordMismatchError()

        new_hash = hash_password(password_data.new_password)

        user = await self.repository.update_password(user, new_hash)
        return user

    async def deactivate_user(self, user_id: int) -> User:
        if self.current_user and self.current_user.id == user_id:
            raise CannotDeactivateSelfError()

        user = await self.repository.get_by_id(user_id, include_inactive=True)
        if not user:
            raise UserNotFoundError(user_id=user_id)

        if not user.is_active:
            return user

        return await self.repository.deactivate(user)

    async def activate_user(self, user_id: int) -> User:
        user = await self.repository.get_by_id(user_id, include_inactive=True)
        if not user:
            raise UserNotFoundError(user_id=user_id)

        if user.is_active:
            return user

        return await self.repository.activate(user)

    async def delete_user(self, user_id: int, permanent: bool = False) -> None:
        if self.current_user and self.current_user.id == user_id:
            if permanent:
                raise CannotDeleteSelfError()

            user = await self.repository.get_by_id(user_id, include_inactive=True)
            if not user:
                raise UserNotFoundError(user_id=user_id)

            if user.is_active:
                await self.repository.deactivate(user)
            return

        user = await self.repository.get_by_id(user_id, include_inactive=True)
        if not user:
            raise UserNotFoundError(user_id=user_id)

        if permanent:
            await self.repository.delete(user)
        else:
            if user.is_active:
                await self.repository.deactivate(user)

    async def get_stats(self) -> dict:
        return await self.repository.get_stats()
