import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import AsyncSessionLocal
from app.users.repository import PermissionRepository, RoleRepository
from app.users.schemas import PermissionCreate, RoleCreate


async def init_permissions(db) -> dict:
    """Создает все базовые разрешения"""
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
    for perm in permissions_config:
        existing = await perm_repo.get_by_name(perm["name"])
        if not existing:
            permission = await perm_repo.create(PermissionCreate(**perm))
            permissions_map[perm["name"]] = permission.id
            print(f"✅ Created permission: {perm['name']}")
        else:
            permissions_map[perm["name"]] = existing.id
            print(f"⚠️  Permission already exists: {perm['name']}")

    return permissions_map


async def init_default_roles(db, permissions_map: dict):
    """Создает роли User и Admin с разрешениями"""
    role_repo = RoleRepository(db)

    # 1. Роль User (дефолтная)
    user_role = await role_repo.get_by_name("user")
    if not user_role:
        user_permission_ids = [
            permissions_map["user:read:own"],
            permissions_map["user:write:own"],
            permissions_map["user:read:any"],
        ]

        user_role = await role_repo.create(
            RoleCreate(
                name="user",
                description="Default user role",
                is_default=True,
                permission_ids=user_permission_ids,
            )
        )
        print("✅ Created default role: user")
    else:
        print("⚠️  Role already exists: user")

    # 2. Роль Admin (не дефолтная)
    admin_role = await role_repo.get_by_name("admin")
    if not admin_role:
        admin_permission_ids = list(permissions_map.values())  # Все разрешения

        admin_role = await role_repo.create(
            RoleCreate(
                name="admin",
                description="Administrator with full permissions",
                is_default=False,
                permission_ids=admin_permission_ids,
            )
        )
        print("✅ Created admin role: admin")
        print("   Permissions granted: All permissions")
    else:
        print("⚠️  Role already exists: admin")

    return {"user_role": user_role, "admin_role": admin_role}


async def main():
    """Основная функция инициализации"""
    print("")
    print("=" * 60)
    print("ROLES & PERMISSIONS INITIALIZATION")
    print("=" * 60)

    async with AsyncSessionLocal() as session:
        try:
            # 1. Создаем разрешения
            print("\nCreating permissions...")
            permissions_map = await init_permissions(session)

            # 2. Создаем роли
            print("\nCreating roles...")
            await init_default_roles(session, permissions_map)

            await session.commit()

            print("\n" + "=" * 60)
            print("✅ INITIALIZATION COMPLETE!")
            print("=" * 60)

            print("\nNext steps:")
            print("1. Run 'python -m app.scripts.create_admin' to create admin user")
            print("2. Use default credentials to login")

        except Exception as e:
            await session.rollback()
            print(f"\n❌ Initialization failed: {e}")
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
