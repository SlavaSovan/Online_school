import asyncio
import time
import sys
import logging
from pathlib import Path

from app.users.services import PermissionService, RoleService

sys.path.insert(0, str(Path(__file__).parent.parent))

import app.core.database as db
from app.users.repository import PermissionRepository, RoleRepository
from app.users.schemas import PermissionCreate, RoleCreate

logger = logging.getLogger(__name__)


async def init_permissions(db) -> dict:
    """Создает все базовые разрешения"""
    perm_service = PermissionService(db)
    perm_repo = PermissionRepository(db)

    permissions_config = [
        {
            "name": "user:read:own",
            "description": "Read own profile",
            "category": "user",
        },
        {
            "name": "user:write:own",
            "description": "Edit own profile",
            "category": "user",
        },
        {
            "name": "user:read:any",
            "description": "Read any user profile",
            "category": "user",
        },
        {
            "name": "user:write:any",
            "description": "Edit any user profile",
            "category": "user",
        },
        {"name": "role:read", "description": "Read roles", "category": "role"},
        {"name": "role:write", "description": "Manage roles", "category": "role"},
        {
            "name": "permission:read",
            "description": "Read permissions",
            "category": "permission",
        },
        {
            "name": "permission:write",
            "description": "Manage permissions",
            "category": "permission",
        },
    ]

    permissions_map = {}

    logger.info(f"Found {len(permissions_config)} permissions to check")

    for perm in permissions_config:
        existing = await perm_repo.get_by_name(perm["name"])
        if not existing:
            permission_create = PermissionCreate(**perm)
            permission = await perm_service.create_permission(permission_create)
            permissions_map[perm["name"]] = permission.id
            logger.info(f"Created permission: {perm['name']}")
        else:
            permissions_map[perm["name"]] = existing.id
            logger.info(f"Permission exists: {perm['name']}")

    logger.info(f"Total permissions: {len(permissions_map)}")
    return permissions_map


async def init_default_roles(db, permissions_map: dict):
    """Создает роли User и Admin с разрешениями"""
    role_service = RoleService(db)
    role_repo = RoleRepository(db)

    defaul_role = await role_repo.get_default_role()
    user_role = await role_repo.get_by_name("user")

    if not defaul_role:
        if not user_role:
            user_permissions = [
                permissions_map["user:read:own"],
                permissions_map["user:write:own"],
                permissions_map["user:read:any"],
            ]

            user_permission_ids = [pid for pid in user_permissions if pid is not None]

            role_create = RoleCreate(
                name="user",
                description="Default user role",
                is_default=True,
                permission_ids=user_permission_ids,
            )
            user_role = await role_service.create_role(role_create)
            logger.info("Created user role with basic permissions")
        else:
            role_service.set_default_role(user_role.id)
            logger.info("Set existing user role as default")

    admin_role = await role_repo.get_by_name("admin")
    if not admin_role:
        admin_permission_ids = list(permissions_map.values())
        role_create = RoleCreate(
            name="admin",
            description="Administrator with full permissions",
            is_default=False,
            permission_ids=admin_permission_ids,
        )
        admin_role = await role_service.create_role(role_create)
        logger.info(f"Created admin role with {len(admin_permission_ids)} permissions")
    else:
        logger.info("Admin role already exists")

    # Special for courses and tasks microservices

    mentor_role = await role_repo.get_by_name("mentor")
    if not mentor_role:
        mentor_permissions = [
            permissions_map["user:read:own"],
            permissions_map["user:write:own"],
            permissions_map["user:read:any"],
        ]

        mentor_permission_ids = [pid for pid in mentor_permissions if pid is not None]

        role_create = RoleCreate(
            name="mentor",
            description="Mentor role with user permissions",
            is_default=False,
            permission_ids=mentor_permission_ids,
        )
        logger.info("Created mentor role with user permissions")

    return {
        "user_role": user_role,
        "admin_role": admin_role,
        "mentor_role": mentor_role,
    }


async def main():
    """Основная функция инициализации"""

    logger.info("=" * 60)
    logger.info("INITIALIZING PERMISSIONS AND ROLES")
    logger.info("=" * 60)

    db.init_db()

    async with db.async_session_maker() as session:
        try:
            # 1. Создаем разрешения
            logger.info("\nStep 1: Creating permissions...")
            permissions_map = await init_permissions(session)

            time.sleep(1)

            # 2. Создаем роли
            logger.info("\n Step 2: Creating roles...")
            await init_default_roles(session, permissions_map)

            await session.commit()

            logger.info("\n" + "=" * 60)
            logger.info("INITIALIZATION COMPLETE!")
            logger.info("=" * 60)

        except Exception as e:
            await session.rollback()
            logger.error(f"Initialization failed: {e}")
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
