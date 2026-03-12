from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "e-Flow Enterprise API"
    api_prefix: str = ""
    database_url: str = "sqlite:///./e_flow_enterprise.db"
    jwt_secret: str = "dev-secret-change-me-enterprise-32-bytes-minimum"
    jwt_algorithm: str = "HS256"
    token_ttl_minutes: int = 720
    storage_dir: str = str(Path(__file__).resolve().parent.parent / "uploads")
    org_id: str = "demo-org"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
