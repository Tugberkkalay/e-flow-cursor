from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://eflow:eflow_secret@localhost:5432/eflow"
    redis_url: str = "redis://localhost:6379"
    secret_key: str = "dev-secret-key-change-in-prod"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440  # 24h
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin123"
    minio_bucket: str = "eflow-docs"
    app_name: str = "e-Flow Enterprise"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
