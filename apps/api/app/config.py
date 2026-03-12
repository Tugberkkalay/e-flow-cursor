from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    APP_NAME: str = "e-Flow Enterprise API"
    DEBUG: bool = True

    DATABASE_URL: str = "sqlite:///./eflow.db"
    SECRET_KEY: str = "eflow-secret-key-change-in-production-2024"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    REDIS_URL: str = "redis://localhost:6379"
    S3_ENDPOINT: str = "http://localhost:9000"
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin"
    S3_BUCKET: str = "eflow-documents"

    ORG_ID: str = "org_1"

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()
