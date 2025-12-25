from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_user_service, get_user_service_for_manage
from app.core.database import get_db

from app.users.models import User
from app.users.services import UserService
from app.users.schemas import (
    PasswordChange,
    UserCreate,
    UserDetailResponse,
    UserResponse,
    UserUpdate,
)

from app.auth.utils import create_access_token, create_refresh_token
from app.auth.repository import RefreshTokenRepository
from app.auth.validation import (
    get_current_active_auth_user,
    get_token_payload,
    get_user_by_token_sub,
    validate_auth_user,
    validate_token_type,
)
from app.auth.schemas import RefreshTokenSchema, LoginSchema, TokenInfo


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def register(
    reg_data: UserCreate,
    user_service: UserService = Depends(get_user_service),
) -> UserResponse:
    user: UserResponse = await user_service.create_user(reg_data)
    return user


@router.post("/login", response_model=TokenInfo)
async def login(
    login_data: LoginSchema, db: AsyncSession = Depends(get_db)
) -> TokenInfo:
    user = await validate_auth_user(login_data, db)

    access = create_access_token(user)
    refresh = create_refresh_token(user)

    payload = get_token_payload(token=refresh)
    refresh_repo = RefreshTokenRepository(db)
    await refresh_repo.save_token(payload["sub"], refresh, payload["exp"])

    return TokenInfo(access_token=access, refresh_token=refresh)


@router.post("/refresh", response_model=TokenInfo)
async def refresh_tokens(
    refresh_data: RefreshTokenSchema = Body(...), db: AsyncSession = Depends(get_db)
):
    payload = get_token_payload(token=refresh_data.refresh_token)
    validate_token_type(payload, "refresh_token")

    refresh_repo = RefreshTokenRepository(db)
    if await refresh_repo.is_token_revoked(refresh_data.refresh_token):
        raise HTTPException(status_code=401, detail="Refresh token revoked or expired")

    user = await get_user_by_token_sub(payload, db)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token subject")

    access = create_access_token(user)
    new_refresh = create_refresh_token(user)
    await refresh_repo.save_token(payload["sub"], new_refresh, payload["exp"])
    await refresh_repo.revoke_token(refresh_data.refresh_token)

    return TokenInfo(access_token=access, refresh_token=new_refresh)


@router.post("/logout")
async def logout(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_auth_user),
):
    refresh_repo = RefreshTokenRepository(db)
    revoked = await refresh_repo.revoke_all_user_tokens(user.id)
    if not revoked:
        raise HTTPException(status_code=400, detail="Refresh token not found")
    return {"message": "Logged out"}


@router.get("/profile", response_model=UserDetailResponse)
async def profile(
    user: User = Depends(get_current_active_auth_user),
    user_service: UserService = Depends(get_user_service),
):
    user_profile = await user_service.get_user_by_id(user.id)
    return user_profile


@router.put("/profile", response_model=UserResponse)
async def update_profile(
    user_data: UserUpdate,
    user: User = Depends(get_current_active_auth_user),
    user_service: UserService = Depends(get_user_service),
):
    return await user_service.update_user(user.id, user_data)


@router.post("/change-password")
async def change_password(
    change_data: PasswordChange,
    user: User = Depends(get_current_active_auth_user),
    user_service: UserService = Depends(get_user_service),
):
    await user_service.change_password(user.id, change_data)
    return {"message": "Password changed successfully"}
