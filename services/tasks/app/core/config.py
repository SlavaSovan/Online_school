from pathlib import Path
from typing import List
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

    @property
    def redis_url(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/1"

    @property
    def redis_cache_url(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/2"


class S3Settings(BaseModel):
    S3_ACCESS_KEY_ID: str
    S3_SECRET_ACCESS_KEY: str
    S3_ENDPOINT_URL: str
    S3_REGION: str
    S3_BUCKET_NAME: str
    S3_PUBLIC_ENDPOINT: str = "http://localhost:9000"


class FileSettings(BaseModel):
    ALLOWED_FILE_TYPES: str = (
        "pdf,doc,docx,xls,xlsx,xlsm,ppt,pptx,pptm,txt,zip,rar,py,java,cpp,c,js,html,css"
    )
    MAX_FILENAME_LENGTH: int = 255
    MAX_FILE_SIZE_MB: int = 40


class Settings(BaseSettings):
    APP_NAME: str = "tasks service"
    DEBUG: bool = True

    CORS_ORIGINS: list[str] = [
        "http://localhost:8003",
        "http://0.0.0.0:8003",
    ]

    API_PREFIX: str = "/api/v1"

    DATABASE: DBSettings
    REDIS: RedisSettings
    S3: S3Settings

    USER_SERVICE_URL: str
    COURSE_SERVICE_URL: str

    FILES: FileSettings = FileSettings()

    model_config = ConfigDict(
        env_nested_delimiter="__",
        extra="ignore",
        # env_file=".env",
    )


settings = Settings()
