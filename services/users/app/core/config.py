from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import BaseModel, ConfigDict


BASE_DIR = Path(__file__).parent.parent


class DBSettings(BaseModel):
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )


class RedisSettings(BaseModel):
    REDIS_HOST: str
    REDIS_PORT: int


class AuthJWT(BaseModel):
    PRIVATE_KEY: Path = BASE_DIR / "certs" / "jwt-private.pem"
    PUBLIC_KEY: Path = BASE_DIR / "certs" / "jwt-public.pem"
    ALG: str = "RS256"

    ACCESS_EXPIRE_MIN: int = 120
    REFRESH_EXPIRE_DAYS: int = 30


class Settings(BaseSettings):
    APP_NAME: str = "auth service"
    DEBUG: bool = True

    CORS_ORIGINS: list[str] = [
        "http://localhost:8001",
        "http://0.0.0.0:8001",
    ]

    API_PREFIX: str = "/api/v1"

    DATABASE: DBSettings
    REDIS: RedisSettings
    AUTH_JWT: AuthJWT = AuthJWT()

    model_config = ConfigDict(
        env_nested_delimiter="__",
        extra="ignore",
    )


settings = Settings()
