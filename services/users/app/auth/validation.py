from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jwt import InvalidTokenError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.schemas import LoginSchema
from app.auth.blacklist import token_blacklist
from app.core.database import get_db
from app.core.utils import decode_jwt, validate_password
from app.users.models import User
from app.users.repository import UserRepository

from .utils import (
    TOKEN_TYPE_FIELD,
    ACCESS_TOKEN_TYPE,
    REFRESH_TOKEN_TYPE,
)


http_bearer = HTTPBearer(auto_error=False)
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login/swagger", auto_error=False
)


async def validate_auth_user(
    login_data: LoginSchema,
    db: AsyncSession = Depends(get_db),
):
    unauthed_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid login or password",
    )
    user_repo = UserRepository(db)
    user = await user_repo.get_by_email(login_data.email)

    if not user:
        raise unauthed_exc

    if not validate_password(
        password=login_data.password, hashed_password=user.hashed_password
    ):
        raise unauthed_exc

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User inactive",
        )

    return user


def get_token_payload(token: str) -> dict:
    try:
        payload = decode_jwt(token=token)
    except InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {e}",
        )
    return payload


def get_current_token_payload(
    token: str = Depends(oauth2_scheme),
) -> dict:
    payload = get_token_payload(token)
    return payload


def validate_token_type(payload: dict, token_type: str) -> bool:
    current_token_type = payload.get(TOKEN_TYPE_FIELD)

    if current_token_type == token_type:
        return True

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=f"Invalid token type {current_token_type!r} expected {token_type!r}",
    )


async def get_user_by_token_sub(
    payload: dict, db: AsyncSession = Depends(get_db)
) -> User:
    user_id = int(payload["sub"])
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload"
        )
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)

    if user:
        return user
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )


async def check_token_blacklist(token: str = Depends(oauth2_scheme)):
    if not token:
        return token

    if await token_blacklist.is_blacklisted(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token


class UserGetterFromToken:
    def __init__(self, token_type: str):
        self.token_type = token_type

    async def __call__(
        self,
        payload: dict = Depends(get_current_token_payload),
        token: str = Depends(oauth2_scheme),
        db: AsyncSession = Depends(get_db),
    ):
        validate_token_type(payload, self.token_type)
        await check_token_blacklist(token)
        return await get_user_by_token_sub(payload, db)


get_current_auth_user_for_access = UserGetterFromToken(ACCESS_TOKEN_TYPE)
get_current_auth_user_for_refresh = UserGetterFromToken(REFRESH_TOKEN_TYPE)


async def get_current_active_auth_user(
    user: User = Depends(get_current_auth_user_for_access),
):
    if user.is_active:
        return user

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="User is inactive",
    )


async def get_current_active_user_with_permissions(
    user: User = Depends(get_current_active_auth_user),
    db: AsyncSession = Depends(get_db),
) -> User:

    from sqlalchemy.orm import selectinload
    from sqlalchemy import select
    from app.users.models import Role

    stmt = (
        select(User)
        .options(selectinload(User.role).selectinload(Role.permissions))
        .where(User.id == user.id)
    )

    result = await db.scalars(stmt)
    user_with_perms = result.one_or_none()
    if not user_with_perms:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    return user_with_perms
