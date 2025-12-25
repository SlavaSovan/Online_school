from typing import Optional
from pydantic import BaseModel


class TokenInfo(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "Bearer"


class LoginSchema(BaseModel):
    identifier: str
    password: str


class RefreshTokenSchema(BaseModel):
    refresh_token: str
