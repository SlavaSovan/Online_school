import os
from dotenv import load_dotenv
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import BaseModel, ConfigDict


load_dotenv()


BASE_DIR = Path(__file__).parent.parent


class DBSettings(BaseModel):
    DB_HOST: str = os.getenv("DB_HOST")
    DB_PORT: str = os.getenv("DB_PORT")
    DB_NAME: str = os.getenv("DB_NAME")
    DB_USER: str = os.getenv("DB_USER")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD")

    model_config = ConfigDict(env_file=".env", extra="ignore")

    @property
    def database_url(self) -> str:
        """URL для подключения к базе данных"""
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"


class AuthJWT(BaseModel):
    PRIVATE_KEY: Path = BASE_DIR / "certs" / "jwt-private.pem"
    PUBLIC_KEY: Path = BASE_DIR / "certs" / "jwt-public.pem"
    ALG: str = "RS256"

    ACCESS_EXPIRE_MIN: int = 120
    REFRESH_EXPIRE_DAYS: int = 30


class Settings(BaseSettings):
    APP_NAME: str = "Users service"
    DEBUG: bool = True

    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]
    STATIC_DIR: str = str(BASE_DIR) + "/static"
    IMAGES_DIR: str = str(BASE_DIR) + "/static/images"

    API_PREFIX: str = "/api/v1"

    DATABASE: DBSettings = DBSettings()
    AUTH_JWT: AuthJWT = AuthJWT()


settings = Settings()
