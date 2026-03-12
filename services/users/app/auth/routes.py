import logging
from datetime import datetime
from fastapi import APIRouter, Body, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_user_service
from app.core.database import get_db

from app.core.utils import decode_jwt
from app.users.exception_handler import handle_user_errors
from app.users.models import User
from app.users.services import UserService
from app.users.schemas import (
    PasswordChange,
    UserCreate,
    UserDetailResponse,
    UserRegister,
    UserResponse,
    UserUpdate,
    UserUpdateProfile,
)

from app.auth.utils import create_access_token, create_refresh_token
from app.auth.repository import RefreshTokenRepository
from app.auth.blacklist import TokenBlacklist, get_token_blacklist
from app.auth.validation import (
    get_current_active_auth_user,
    get_token_payload,
    get_user_by_token_sub,
    validate_auth_user,
    validate_token_type,
)
from app.auth.schemas import RefreshTokenSchema, LoginSchema, TokenInfo


logger = logging.getLogger(__name__)


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
@handle_user_errors
async def register(
    reg_data: UserRegister,
    user_service: UserService = Depends(get_user_service),
) -> UserResponse:
    data_dict = reg_data.model_dump(exclude_unset=True)
    user_data = UserCreate(**data_dict)
    user: UserResponse = await user_service.create_user(user_data)
    return UserResponse.model_validate(user)


@router.get("/profile", response_model=UserDetailResponse)
@handle_user_errors
async def profile(
    current_user: User = Depends(get_current_active_auth_user),
    user_service: UserService = Depends(get_user_service),
):
    user = await user_service.get_user_by_id(current_user.id, include_inactive=False)
    return UserDetailResponse.model_validate(user)


@router.patch("/profile", response_model=UserResponse)
@handle_user_errors
async def update_profile(
    user_data: UserUpdateProfile,
    current_user: User = Depends(get_current_active_auth_user),
    user_service: UserService = Depends(get_user_service),
):
    data_dict = user_data.model_dump(exclude_unset=True)
    update_data = UserUpdate(**data_dict)
    user_service.current_user = current_user
    user = await user_service.update_user(current_user.id, update_data)
    return UserResponse.model_validate(user)


@router.post("/change-password")
@handle_user_errors
async def change_password(
    change_data: PasswordChange,
    current_user: User = Depends(get_current_active_auth_user),
    user_service: UserService = Depends(get_user_service),
):
    user_service.current_user = current_user
    await user_service.change_password(current_user.id, change_data)
    return {"message": "Password changed successfully"}


@router.delete("/profile", status_code=status.HTTP_204_NO_CONTENT)
@handle_user_errors
async def delete_own_account(
    current_user: User = Depends(get_current_active_auth_user),
    user_service: UserService = Depends(get_user_service),
):
    user_service.current_user = current_user
    await user_service.delete_user(current_user.id, permanent=False)


@router.post("/login", response_model=TokenInfo)
async def login(
    login_data: LoginSchema, db: AsyncSession = Depends(get_db)
) -> TokenInfo:
    user = await validate_auth_user(login_data, db)

    access = create_access_token(user)
    refresh = create_refresh_token(user)

    payload = get_token_payload(token=refresh)
    refresh_repo = RefreshTokenRepository(db)
    await refresh_repo.save_token(
        usr_id=str(user.id), token=refresh, exp=payload["exp"]
    )

    return TokenInfo(access_token=access, refresh_token=refresh)


@router.post("/login/swagger", response_model=TokenInfo)
async def login_swagger(
    form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
) -> TokenInfo:
    """Login endpoint for Swagger UI"""
    login_data = LoginSchema(
        email=form_data.username,
        password=form_data.password,
    )

    user = await validate_auth_user(login_data, db)
    access_token = create_access_token(user)
    refresh_token = create_refresh_token(user)

    payload = get_token_payload(refresh_token)
    refresh_repo = RefreshTokenRepository(db)
    await refresh_repo.save_token(str(user.id), refresh_token, payload["exp"])

    return TokenInfo(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenInfo)
async def refresh_tokens(
    refresh_data: RefreshTokenSchema = Body(...),
    db: AsyncSession = Depends(get_db),
    blacklist: TokenBlacklist = Depends(get_token_blacklist),
):
    refresh_token = refresh_data.refresh_token

    try:
        payload = get_token_payload(token=refresh_token)
    except HTTPException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    validate_token_type(payload, "refresh_token")

    if await blacklist.is_blacklisted(refresh_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has been revoked",
        )

    refresh_repo = RefreshTokenRepository(db)
    if await refresh_repo.is_token_revoked(refresh_token):
        await blacklist.add_to_blacklist(refresh_token, 7 * 24 * 60 * 60)  # 7 дней
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token revoked or expired",
        )

    user = await get_user_by_token_sub(payload, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token subject",
        )

    access = create_access_token(user)
    new_refresh = create_refresh_token(user)

    new_payload = get_token_payload(new_refresh)
    exp_timestamp = new_payload["exp"]
    if isinstance(exp_timestamp, datetime):
        exp_timestamp = exp_timestamp.timestamp()

    await refresh_repo.save_token(
        usr_id=str(user.id), token=new_refresh, exp=exp_timestamp
    )

    await refresh_repo.revoke_token(refresh_token)

    await blacklist.add_to_blacklist(refresh_token, 7 * 24 * 60 * 60)

    return TokenInfo(access_token=access, refresh_token=new_refresh)


@router.post("/logout")
async def logout(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_auth_user),
    blacklist: TokenBlacklist = Depends(get_token_blacklist),
):
    refresh_repo = RefreshTokenRepository(db)

    revoked = await refresh_repo.revoke_all_user_tokens(user.id)
    if not revoked:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Refresh token not found",
        )

    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        access_token = auth_header.replace("Bearer ", "")

        try:
            payload = decode_jwt(access_token)
            exp = payload.get("exp")
            if exp:
                now = datetime.now().timestamp()
                expires_in = max(0, int(exp - now))
                if expires_in > 0:
                    await blacklist.add_to_blacklist(access_token, expires_in, "access")
        except Exception as e:
            logger.error(f"Failed to blacklist access token: {e}")
    return {"message": "Logged out"}
