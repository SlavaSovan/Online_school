import jwt
import bcrypt
from datetime import datetime, timedelta, timezone

from .config import settings


def encode_jwt(
    payload: dict,
    private_key: str = settings.AUTH_JWT.PRIVATE_KEY.read_text(),
    algorythm: str = settings.AUTH_JWT.ALG,
    expire_timedelta: timedelta | None = None,
    expire_minutes: int = settings.AUTH_JWT.ACCESS_EXPIRE_MIN,
):

    to_encode = payload.copy()
    now = datetime.now(timezone.utc)

    if expire_timedelta:
        expire = now + expire_timedelta
    else:
        expire = now + timedelta(minutes=expire_minutes)

    to_encode.update(iat=now, exp=expire)
    encoded = jwt.encode(to_encode, private_key, algorithm=algorythm)

    return encoded


def decode_jwt(
    token: str | bytes,
    public_key: str = settings.AUTH_JWT.PUBLIC_KEY.read_text(),
    algorithm: str = settings.AUTH_JWT.ALG,
):

    decoded = jwt.decode(token, public_key, algorithms=[algorithm])
    return decoded


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def validate_password(password: str, hashed_password: str) -> bool:
    if isinstance(hashed_password, str):
        hashed_bytes = hashed_password.encode("utf-8")
    else:
        hashed_bytes = hashed_password
    return bcrypt.checkpw(password.encode("utf-8"), hashed_bytes)
