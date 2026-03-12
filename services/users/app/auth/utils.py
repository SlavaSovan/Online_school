from datetime import timedelta
import hashlib
from app.core.utils import encode_jwt
from app.users.models import User
from ..core.config import settings


TOKEN_TYPE_FIELD = "type"
ACCESS_TOKEN_TYPE = "access_token"
REFRESH_TOKEN_TYPE = "refresh_token"


def create_jwt(
    token_type: str,
    token_data: dict,
    expire_minutes: int = settings.AUTH_JWT.ACCESS_EXPIRE_MIN,
    expire_timedelta: timedelta | None = None,
) -> str:
    jwt_payload = {TOKEN_TYPE_FIELD: token_type}
    jwt_payload.update(token_data)
    token = encode_jwt(
        payload=jwt_payload,
        expire_minutes=expire_minutes,
        expire_timedelta=expire_timedelta,
    )
    return token


def create_access_token(user: User) -> str:
    jwt_payload = {
        "sub": str(user.id),
        "email": user.email,
        "role_id": user.role_id,
    }
    return create_jwt(
        token_type=ACCESS_TOKEN_TYPE,
        token_data=jwt_payload,
        expire_minutes=settings.AUTH_JWT.ACCESS_EXPIRE_MIN,
    )


def create_refresh_token(user: User) -> str:
    jwt_payload = {
        "sub": str(user.id),
        "email": user.email,
        "role_id": user.role_id,
    }
    return create_jwt(
        token_type=REFRESH_TOKEN_TYPE,
        token_data=jwt_payload,
        expire_timedelta=timedelta(days=settings.AUTH_JWT.REFRESH_EXPIRE_DAYS),
    )


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
