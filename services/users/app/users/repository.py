from typing import List, Optional, Sequence
from sqlalchemy import func, select, update
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.users.models import Permission, User, Role
from app.users.schemas import (
    PermissionCreate,
    PermissionResponse,
    PermissionUpdate,
    RoleCreate,
    RoleUpdate,
    UserCreate,
    UserUpdate,
)


class PermissionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self) -> Sequence[Permission]:
        stmt = select(Permission).order_by(Permission.category, Permission.name)
        result = await self.db.scalars(stmt)
        return result.all()

    async def get_by_id(self, permission_id: int) -> Optional[Permission]:
        stmt = select(Permission).where(Permission.id == permission_id)
        result = await self.db.scalars(stmt)
        return result.one_or_none()

    async def get_by_name(self, name: str) -> Optional[Permission]:
        stmt = select(Permission).where(Permission.name == name)
        result = await self.db.scalars(stmt)
        return result.one_or_none()

    async def get_by_category(self, category: str) -> Sequence[Permission]:
        stmt = select(Permission).where(Permission.category == category)
        result = await self.db.scalars(stmt)
        return result.all()

    async def create(self, permission_data: PermissionCreate) -> Permission:
        permission = Permission(**permission_data.model_dump())
        self.db.add(permission)
        await self.db.commit()
        await self.db.refresh(permission)
        return permission

    async def update(
        self, permission_id: int, permission_data: PermissionUpdate
    ) -> Optional[PermissionResponse]:
        permission = await self.get_by_id(permission_id)
        if not permission:
            return None

        update_data = permission_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(permission, field, value)

        await self.db.commit()
        await self.db.refresh(permission)
        return permission

    async def delete(self, permission_id: int) -> bool:
        permission = await self.get_by_id(permission_id)
        if permission:
            await self.db.delete(permission)
            await self.db.commit()
            return True
        return False

    async def has_role_dependencies(self, permission_id: int) -> bool:
        from app.users.models import RolePermission

        stmt = select(RolePermission).where(
            RolePermission.permission_id == permission_id
        )

        result = await self.db.scalars(stmt)
        return result.first() is not None


class RoleRepository:
    def __init__(self, db: AsyncSession):
        self.db: AsyncSession = db

    async def get_all(self) -> Sequence[Role]:
        stmt = select(Role)
        result = await self.db.scalars(stmt)
        return result.all()

    async def get_by_id(self, role_id: int) -> Optional[Role]:
        stmt = (
            select(Role)
            .where(Role.id == role_id)
            .options(selectinload(Role.permissions))
        )
        result = await self.db.scalars(stmt)
        return result.one_or_none()

    async def get_by_name(self, name: str) -> Optional[Role]:
        stmt = select(Role).where(Role.name == name)
        result = await self.db.scalars(stmt)
        return result.one_or_none()

    async def get_default_role(self) -> Optional[Role]:
        stmt = select(Role).where(Role.is_default == True)
        result = await self.db.scalars(stmt)
        return result.one_or_none()

    async def create(self, role_data: RoleCreate) -> Role:
        if role_data.is_default:
            await self._reset_default_roles(commit=False)

        role = Role(
            name=role_data.name,
            description=role_data.description,
            is_default=role_data.is_default,
        )
        self.db.add(role)

        if role_data.permission_ids:
            stmt = select(Permission).where(Permission.id.in_(role_data.permission_ids))
            result = await self.db.scalars(stmt)
            permissions = result.all()

            for permission in permissions:
                role.permissions.append(permission)

        await self.db.commit()
        await self.db.refresh(role)
        return role

    async def update(self, role_id: int, role_data: RoleUpdate) -> Optional[Role]:
        role = await self.get_by_id(role_id)
        if not role:
            return None

        if role_data.is_default and not role.is_default:
            await self._reset_default_roles(commit=False)

        update_data = role_data.model_dump(
            exclude_unset=True, exclude={"permission_ids"}
        )
        for field, value in update_data.items():
            setattr(role, field, value)

        if role_data.permission_ids is not None:
            await self._set_role_permissions_internal(role, role_data.permission_ids)

        await self.db.commit()
        await self.db.refresh(role)
        return role

    async def delete(self, role_id: int) -> bool:
        role = await self.get_by_id(role_id)

        if not role:
            return False

        if role.is_default:
            raise ValueError("Cannot delete default role")

        user_count = await self._count_users_with_role(role_id)
        if user_count > 0:
            raise ValueError(f"Cannot delete role with {user_count} users")

        await self.db.delete(role)
        await self.db.commit()
        return True

    async def set_default_role(self, role_id: int) -> Role:
        role = await self.get_by_id(role_id)
        if not role:
            raise ValueError(f"Role with id {role_id} not found")

        await self._reset_default_roles()

        role.is_default = True

        await self.db.commit()
        await self.db.refresh(role)
        return role

    async def _reset_default_roles(self, commit: bool = True):
        stmt = update(Role).where(Role.is_default == True).values(is_default=False)
        await self.db.execute(stmt)

        if commit:
            await self.db.commit()

    async def add_permission_to_role(self, role_id: int, permission_id: int) -> Role:
        role = await self.get_by_id(role_id)
        permission = await PermissionRepository(self.db).get_by_id(permission_id)

        if role and permission and permission not in role.permissions:
            role.permissions.append(permission)
            await self.db.commit()
            await self.db.refresh(role)
        return role

    async def remove_permission_from_role(
        self, role_id: int, permission_id: int
    ) -> Role:
        role = await self.get_by_id(role_id)
        permission = await PermissionRepository(self.db).get_by_id(permission_id)

        if role and permission and permission in role.permissions:
            role.permissions.remove(permission)
            await self.db.commit()
            await self.db.refresh(role)
        return role

    async def set_role_permissions(
        self, role_id: int, permission_ids: List[int]
    ) -> Role:
        role = await self.get_by_id(role_id)

        if not role:
            raise ValueError(f"Role with id {role_id} not found")

        role.permissions.clear()

        permission_repo = PermissionRepository(self.db)
        for perm_id in permission_ids:
            permission = await permission_repo.get_by_id(perm_id)
            if permission:
                role.permissions.append(permission)

        await self.db.commit()
        await self.db.refresh(role)
        return role

    async def _set_role_permissions_internal(
        self, role: Role, permission_ids: List[int]
    ):
        """Внутренний метод для установки разрешений без коммита"""
        role.permissions.clear()

        if permission_ids:
            stmt = select(Permission).where(Permission.id.in_(permission_ids))
            result = await self.db.scalars(stmt)
            permissions = result.all()

            for permission in permissions:
                role.permissions.append(permission)

    async def _count_users_with_role(self, role_id: int) -> int:
        stmt = select(func.count(User.id)).where(User.role_id == role_id)
        result = await self.db.scalar(stmt)
        return result


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self) -> Sequence[User]:
        stmt = select(User)
        result = await self.db.scalars(stmt)
        return result.all()

    async def get_by_id(self, user_id: int) -> Optional[User]:
        stmt = select(User).where(User.id == user_id).options(joinedload(User.role))
        result = await self.db.scalars(stmt)
        return result.one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        stmt = select(User).where(User.email == email)
        result = await self.db.scalars(stmt)
        return result.one_or_none()

    async def get_by_username(self, username: str) -> Optional[User]:
        stmt = select(User).where(User.username == username)
        result = await self.db.scalars(stmt)
        return result.one_or_none()

    async def get_by_identifier(self, identifier: str) -> Optional[User]:
        stmt = select(User).where(
            (User.email == identifier) | (User.username == identifier)
        )
        result = await self.db.scalars(stmt)
        return result.one_or_none()

    async def get_by_role(self, role_id) -> Sequence[User]:
        stmt = (
            select(User).options(joinedload(User.role)).where(User.role_id == role_id)
        )
        result = await self.db.scalars(stmt)
        return result.all()

    def user_exists(self, user: User, exclude_user_id: Optional[int] = None) -> bool:
        return user and user.id != exclude_user_id

    async def is_email_taken(
        self, email: str, exclude_user_id: Optional[int] = None
    ) -> bool:
        user = await self.get_by_email(email)
        exists = self.user_exists(user, exclude_user_id)
        return exists

    async def is_username_taken(
        self, username: Optional[str] = None, exclude_user_id: Optional[int] = None
    ) -> bool:
        if not username:
            return False

        user = await self.get_by_username(username)
        exists = self.user_exists(user, exclude_user_id)
        return exists

    async def create(
        self, user_data: UserCreate, hashed_password: str, role_id: Optional[int] = None
    ) -> User:
        user = User(
            email=user_data.email,
            username=user_data.username,
            hashed_password=hashed_password,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            role_id=role_id,
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def update(self, user_id: int, user_data: UserUpdate) -> Optional[User]:
        user = await self.get_by_id(user_id)
        if user:
            for field, value in user_data.model_dump(exclude_unset=True).items():
                setattr(user, field, value)
            await self.db.commit()
            await self.db.refresh(user)
        return user

    async def update_password(self, user_id: int, new_hash: str) -> Optional[User]:
        user = await self.get_by_id(user_id)
        if user:
            user.hashed_password = new_hash
            await self.db.commit()
            await self.db.refresh(user)
        return user

    async def delete(self, user_id: int) -> bool:
        user = await self.get_by_id(user_id)
        if user:
            await self.db.delete(user)
            await self.db.commit()
            return True
        return False
