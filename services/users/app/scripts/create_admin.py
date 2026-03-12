import asyncio
import getpass
import logging
import re
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

import app.core.database as db
from app.users.models import Role, User
from app.users.schemas import UserCreate
from app.users.repository import RoleRepository, UserRepository
from app.users.services import UserService


logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)


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
        logger.error("Admin role no found!")
        return None

    return admin_role


async def check_existing_admin(db, email: str) -> Optional[User]:
    user_repo = UserRepository(db)
    existing_user = await user_repo.get_by_email(email)

    if existing_user:
        logger.warning(f"User with email '{email}' already exists!")
        return existing_user

    return None


async def create_admin_user(
    db,
    email: str,
    first_name: str,
    last_name: str,
    patronymic: str,
    password: str,
    admin_role,
):
    """Создает пользователя администратора"""
    user_serv = UserService(db)

    user_data = UserCreate(
        email=email,
        first_name=first_name,
        last_name=last_name,
        patronymic=patronymic,
        password=password,
        password_confirm=password,
        role_id=admin_role.id,
    )

    admin_user = await user_serv.create_user(user_data)

    return admin_user


def get_user_input():
    logger.info("")
    logger.info("=" * 60)
    logger.info("ADMIN USER CREATION")
    logger.info("=" * 60)

    while True:
        email: str = input("\nEmail: ").strip()
        if validate_email(email):
            break
        logger.error("Invalid email format. Please try again.")

    while True:
        password: str = getpass.getpass("Password: ")
        confirm_password: str = getpass.getpass("Confirm password: ")

        if password != confirm_password:
            logger.error("Passwords don't match. Please try again.")
            continue

        is_valid, message = validate_password(password)
        if is_valid:
            break
        logger.error(f"{message}. Please try again.")

    first_name: str = input("First name (optional): ").strip()
    last_name: str = input("Last name (optional): ").strip()
    patronymic: str = input("Patronymic (optional): ").strip()

    return {
        "email": email,
        "first_name": first_name or None,
        "last_name": last_name or None,
        "patronymic": patronymic or None,
        "password": password,
    }


async def main():
    print("Setting up administrator account...")

    db.init_db()

    async with db.async_session_maker() as session:
        try:
            admin_role: Optional[Role] = await get_admin_role(session)
            if not admin_role:
                sys.exit(1)

            user_data = get_user_input()

            existing_user = await check_existing_admin(session, user_data["email"])
            if existing_user:
                logger.warning(f"Existing user found:")
                logger.info(f"    Email: {existing_user.email}")
                logger.info(f"    Role: {existing_user.role.name}")

                update = (
                    input("\nUpdate this user to admin role? (y/n): ").strip().lower()
                )
                if update == "y":
                    existing_user.role_id = admin_role.id
                    await session.commit()
                    logger.info("User updated to admin role!")
                else:
                    logger.errior("Operation cancelled.")
                return

            logger.info("")
            logger.info("=" * 60)
            logger.info("CONFIRM ADMIN CREATION")
            logger.info("=" * 60)
            logger.info("")
            logger.info(f"Email: {user_data['email']}")
            if user_data["first_name"]:
                logger.info(f"First name: {user_data['first_name']}")
            if user_data["last_name"]:
                logger.info(f"Last name: {user_data['last_name']}")
            if user_data["patronymic"]:
                logger.info(f"Last name: {user_data['last_name']}")

            confirm = (
                input("\nCreate admin user with these details? (y/n): ").strip().lower()
            )
            if confirm != "y":
                logger.error("Operation cancelled.")
                return

            logger.info("Creating admin user...")
            admin_user = await create_admin_user(
                session, **user_data, admin_role=admin_role
            )

            user_serv = UserService(session)
            admin_detail = await user_serv.get_user_by_id(admin_user.id)

            await session.commit()

            logger.info("")
            logger.info("=" * 60)
            logger.info("ADMIN USER CREATED SUCCESSFULLY!")
            logger.info("=" * 60)
            logger.info("")
            logger.info(f"Administrator credentials:")
            logger.info(f"    Email: {admin_detail.email}")
            if admin_detail.first_name:
                logger.info(
                    f"    Name: {admin_detail.first_name or ''} {admin_detail.last_name or ''} {admin_detail.patronymic or ''}"
                )
            logger.info(f"    Role: {admin_detail.role.name}")
            logger.info(f"    User ID: {admin_detail.id}")

            logger.info("")
            logger.info("IMPORTANT: Save these credentials securely!")
            logger.info("You will need them to login and manage the system.")

        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to create admin user: {e}")
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
