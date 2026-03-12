from typing import List, Optional, Tuple
from sqlalchemy import func, select, update
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.users.models import Permission, User, Role


class PermissionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self) -> List[Permission]:
        stmt = select(Permission).order_by(Permission.category, Permission.name)
        result = await self.db.scalars(stmt)
        return list(result.all())

    async def get_by_id(self, permission_id: int) -> Optional[Permission]:
        stmt = select(Permission).where(Permission.id == permission_id)
        result = await self.db.scalars(stmt)
        return result.one_or_none()

    async def get_by_name(self, name: str) -> Optional[Permission]:
        stmt = select(Permission).where(Permission.name == name)
        result = await self.db.scalars(stmt)
        return result.one_or_none()

    async def get_by_ids(self, permission_ids: List[int]) -> List[Permission]:
        stmt = select(Permission).where(Permission.id.in_(permission_ids))
        result = await self.db.scalars(stmt)
        return list(result.all())

    async def create(self, permission_data: dict) -> Permission:
        permission = Permission(**permission_data)
        self.db.add(permission)
        await self.db.commit()
        await self.db.refresh(permission)
        return permission

    async def update(self, permission: Permission, update_data: dict) -> Permission:
        for field, value in update_data.items():
            setattr(permission, field, value)
        await self.db.commit()
        await self.db.refresh(permission)
        return permission

    async def delete(self, permission: Permission) -> bool:
        await self.db.delete(permission)
        await self.db.commit()

    async def has_role_dependencies(self, permission_id: int) -> bool:
        from app.users.models import RolePermission

        stmt = (
            select(RolePermission)
            .where(RolePermission.permission_id == permission_id)
            .limit(1)
        )

        result = await self.db.scalars(stmt)
        return result.first() is not None


class RoleRepository:
    def __init__(self, db: AsyncSession):
        self.db: AsyncSession = db

    async def get_all(self) -> List[Role]:
        stmt = select(Role)
        result = await self.db.scalars(stmt)
        return list(result.all())

    async def get_all_with_stats(self) -> List[tuple[Role, int]]:
        stmt = (
            select(Role, func.count(User.id).label("user_count"))
            .outerjoin(User, Role.id == User.role_id)
            .group_by(Role.id)
            .order_by(Role.name)
        )

        result = await self.db.execute(stmt)
        return [(role, count) for role, count in result]

    async def get_by_id(self, role_id: int) -> Optional[Role]:
        stmt = (
            select(Role)
            .where(Role.id == role_id)
            .options(selectinload(Role.permissions))
        )
        result = await self.db.scalars(stmt)
        return result.one_or_none()

    async def get_by_id_with_details(
        self, role_id: int
    ) -> Optional[tuple[Role, int, List[Permission]]]:
        stmt_role = (
            select(Role)
            .where(Role.id == role_id)
            .options(selectinload(Role.permissions))
        )
        result_role = await self.db.scalars(stmt_role)
        role = result_role.one_or_none()

        if not role:
            return None

        # Получаем количество пользователей отдельным запросом (всего 2 запроса вместо N+1)
        stmt_count = select(func.count(User.id)).where(User.role_id == role_id)
        user_count = await self.db.scalar(stmt_count) or 0

        return role, user_count, role.permissions

    async def get_by_name(self, name: str) -> Optional[Role]:
        stmt = select(Role).where(Role.name == name)
        result = await self.db.scalars(stmt)
        return result.one_or_none()

    async def get_default_role(self) -> Optional[Role]:
        stmt = select(Role).where(Role.is_default == True)
        result = await self.db.scalars(stmt)
        return result.one_or_none()

    async def create(
        self, role_data: dict, permissions: List[Permission] = None
    ) -> Role:
        role = Role(**role_data)
        self.db.add(role)

        if permissions:
            role.permissions.extend(permissions)

        await self.db.commit()
        await self.db.refresh(role)
        return role

    async def update(self, role: Role, update_data: dict) -> Role:
        for field, value in update_data.items():
            setattr(role, field, value)
        await self.db.commit()
        await self.db.refresh(role)
        return role

    async def delete(self, role: Role) -> None:
        await self.db.delete(role)
        await self.db.commit()

    async def set_permissions(self, role: Role, permissions: List[Permission]) -> Role:
        role.permissions = permissions
        await self.db.commit()
        await self.db.refresh(role)
        return role

    async def add_permission(self, role: Role, permission: Permission) -> Role:
        if permission not in role.permissions:
            role.permissions.append(permission)
            await self.db.commit()
            await self.db.refresh(role)
        return role

    async def remove_permission(self, role: Role, permission: Permission) -> Role:
        if permission in role.permissions:
            role.permissions.remove(permission)
            await self.db.commit()
            await self.db.refresh(role)
        return role

    async def reset_default_roles(self, exclude_role_id: int = None) -> None:
        stmt = update(Role).where(Role.is_default == True)
        if exclude_role_id:
            stmt = stmt.where(Role.id != exclude_role_id)
        stmt = stmt.values(is_default=False)
        await self.db.execute(stmt)
        await self.db.commit()

    async def count_users_by_role(self, role_id: int) -> int:
        stmt = select(func.count(User.id)).where(User.role_id == role_id)
        return await self.db.scalar(stmt) or 0

    async def count_users_by_roles(self, role_ids: List[int]) -> dict[int, int]:
        if not role_ids:
            return {}

        stmt = (
            select(User.role_id, func.count(User.id).label("user_count"))
            .where(User.role_id.in_(role_ids))
            .group_by(User.role_id)
        )

        result = await self.db.execute(stmt)
        return {role_id: count for role_id, count in result}


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(
        self, skip: int = 0, limit: int = 100, include_inactive: bool = False
    ) -> Tuple[List[User], int]:
        stmt = select(User)

        if not include_inactive:
            stmt = stmt.where(User.is_active == True)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = await self.db.scalar(count_stmt) or 0

        stmt = (
            stmt.options(joinedload(User.role))
            .offset(skip)
            .limit(limit)
            .order_by(User.id)
        )
        result = await self.db.scalars(stmt)
        users = list(result.all())

        return users, total

    async def get_by_id(
        self, user_id: int, include_inactive: bool = False
    ) -> Optional[User]:
        stmt = select(User).where(User.id == user_id).options(joinedload(User.role))

        if not include_inactive:
            stmt = stmt.where(User.is_active == True)

        result = await self.db.scalars(stmt)
        return result.one_or_none()

    async def get_by_email(
        self, email: str, include_inactive: bool = False
    ) -> Optional[User]:
        stmt = select(User).where(User.email == email)

        if not include_inactive:
            stmt = stmt.where(User.is_active == True)

        result = await self.db.scalars(stmt)
        return result.one_or_none()

    async def get_by_role(
        self,
        role_id: int,
        skip: int = 0,
        limit: int = 100,
        include_inactive: bool = False,
    ) -> Tuple[List[User], int]:
        stmt = select(User).where(User.role_id == role_id)

        if not include_inactive:
            stmt = stmt.where(User.is_active == True)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = await self.db.scalar(count_stmt) or 0

        stmt = (
            stmt.options(joinedload(User.role))
            .offset(skip)
            .limit(limit)
            .order_by(User.id)
        )
        result = await self.db.scalars(stmt)
        users = list(result.all())

        return users, total

    async def create(
        self,
        email: str,
        hashed_password: str,
        role_id: int,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        patronymic: Optional[str] = None,
    ) -> User:
        user = User(
            email=email,
            hashed_password=hashed_password,
            role_id=role_id,
            first_name=first_name,
            last_name=last_name,
            patronymic=patronymic,
            is_active=True,
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def update(self, user: User, **kwargs) -> User:
        for field, value in kwargs.items():
            if value is not None:
                setattr(user, field, value)

        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def update_password(self, user: User, new_hashed_password: str) -> User:
        user.hashed_password = new_hashed_password
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def deactivate(self, user: User) -> User:
        user.is_active = False
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def activate(self, user: User) -> User:
        user.is_active = True
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def delete(self, user: User) -> None:
        await self.db.delete(user)
        await self.db.commit()

    async def is_email_taken(
        self, email: str, exclude_user_id: Optional[int] = None
    ) -> bool:
        stmt = select(User).where(User.email == email)

        if exclude_user_id:
            stmt = stmt.where(User.id != exclude_user_id)

        result = await self.db.scalars(stmt)
        return result.first() is not None

    async def get_stats(self) -> dict:
        # Общее количество активных пользователей
        total_active = (
            await self.db.scalar(
                select(func.count(User.id)).where(User.is_active == True)
            )
            or 0
        )

        # Общее количество неактивных пользователей
        total_inactive = (
            await self.db.scalar(
                select(func.count(User.id)).where(User.is_active == False)
            )
            or 0
        )

        # Количество пользователей по ролям
        stmt = (
            select(Role.name, func.count(User.id).label("count"))
            .outerjoin(User, Role.id == User.role_id)
            .where(User.is_active == True)
            .group_by(Role.name)
        )

        result = await self.db.execute(stmt)
        by_role = {role: count for role, count in result}

        return {
            "total_active": total_active,
            "total_inactive": total_inactive,
            "by_role": by_role,
        }
