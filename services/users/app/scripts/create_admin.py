"""
Интерактивное создание администратора.
Запускать после init_roles.py.
"""

import asyncio
import getpass
import re
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import AsyncSessionLocal
from app.core.utils import hash_password
from app.users.models import Role, User
from app.users.schemas import UserCreate, UserDetailResponse
from app.users.repository import RoleRepository, UserRepository
from app.users.services import UserService


def validate_email(email: str) -> bool:
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def validate_password(password: str) -> tuple[bool, str]:
    if len(password) < 8:
        return False, "Password must be at least 8 characters"

    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"

    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"

    if not re.search(r"\d", password):
        return False, "Password must contain at least one number"

    return True, ""


async def get_admin_role(db) -> Optional[Role]:
    role_repo = RoleRepository(db)
    admin_role = await role_repo.get_by_name("admin")

    if not admin_role:
        print("\n❌ Admin role not found!")
        print("Please run 'python -m app.scripts.init_roles' first")
        return None

    return admin_role


async def check_existing_admin(db, email: str) -> Optional[User]:
    user_repo = UserRepository(db)
    existing_user = await user_repo.get_by_email(email)

    if existing_user:
        print(f"\n⚠️  User with email '{email}' already exists!")
        return existing_user

    return None


async def create_admin_user(
    db,
    email: str,
    username: str,
    first_name: str,
    last_name: str,
    password: str,
    admin_role,
):
    """Создает пользователя администратора"""
    user_serv = UserService(db)

    user_data = UserCreate(
        email=email,
        username=username,
        first_name=first_name,
        last_name=last_name,
        password=password,
        password_confirm=password,
        role_id=admin_role.id,
    )

    admin_user = await user_serv.create_user(user_data)

    return admin_user


def get_user_input():
    print("\n" + "=" * 60)
    print("ADMIN USER CREATION")
    print("=" * 60)

    while True:
        email: str = input("\nEmail: ").strip()
        if validate_email(email):
            break
        print("❌ Invalid email format. Please try again.")

    while True:
        password: str = getpass.getpass("Password: ")
        confirm_password: str = getpass.getpass("Confirm password: ")

        if password != confirm_password:
            print("❌ Passwords don't match. Please try again.")
            continue

        is_valid, message = validate_password(password)
        if is_valid:
            break
        print(f"❌ {message}. Please try again.")

    username: str = input("Username (optional, press Enter to skip): ").strip()
    first_name: str = input("First name (optional): ").strip()
    last_name: str = input("Last name (optional): ").strip()

    return {
        "email": email,
        "username": username or None,
        "first_name": first_name or None,
        "last_name": last_name or None,
        "password": password,
    }


async def main():
    print("Setting up administrator account...")

    async with AsyncSessionLocal() as session:
        try:
            admin_role: Optional[Role] = await get_admin_role(session)
            if not admin_role:
                sys.exit(1)

            user_data = get_user_input()

            existing_user = await check_existing_admin(session, user_data["email"])
            if existing_user:
                print(f"\nExisting user found:")
                print(f"    Email: {existing_user.email}")
                print(f"    Role: {existing_user.role.name}")

                update = (
                    input("\nUpdate this user to admin role? (y/n): ").strip().lower()
                )
                if update == "y":
                    existing_user.role_id = admin_role.id
                    await session.commit()
                    print("\n✅ User updated to admin role!")
                else:
                    print("\n❌ Operation cancelled.")
                return

            print("\n" + "=" * 60)
            print("CONFIRM ADMIN CREATION")
            print("=" * 60)
            print(f"Email: {user_data['email']}")
            print(f"Username: {user_data['username']}")
            if user_data["first_name"]:
                print(f"First name: {user_data['first_name']}")
            if user_data["last_name"]:
                print(f"Last name: {user_data['last_name']}")

            confirm = (
                input("\n❓ Create admin user with these details? (y/n): ")
                .strip()
                .lower()
            )
            if confirm != "y":
                print("\n❌ Operation cancelled.")
                return

            print("\nCreating admin user...")
            admin_user = await create_admin_user(
                session, **user_data, admin_role=admin_role
            )

            user_serv = UserService(session)
            admin_detail = await user_serv.get_user_by_id(admin_user.id)

            await session.commit()

            print("\n" + "=" * 60)
            print("✅ ADMIN USER CREATED SUCCESSFULLY!")
            print("=" * 60)
            print(f"\nAdministrator credentials:")
            print(f"    Email: {admin_detail.email}")
            print(f"    Username: {admin_detail.username}")
            if admin_detail.first_name:
                print(
                    f"    Name: {admin_detail.first_name} {admin_detail.last_name or ''}"
                )
            print(f"    Role: {admin_detail.role.name}")
            print(f"    User ID: {admin_detail.id}")

            print("\nIMPORTANT: Save these credentials securely!")
            print("You will need them to login and manage the system.")

        except Exception as e:
            await session.rollback()
            print(f"\n❌ Failed to create admin user: {e}")
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
