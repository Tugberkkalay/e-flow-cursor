from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "e-Flow Enterprise API"
    secret_key: str = "change-this-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 8
    database_url: str = "sqlite:///./eflow.db"
    default_org_id: str = "org_default"


@lru_cache
def get_settings() -> Settings:
    return Settings()
