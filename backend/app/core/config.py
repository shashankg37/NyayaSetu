from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    project_name: str = "Nyaya Setu API"
    env: str = "development"
    api_v1_str: str = "/api/v1"
    database_url: str = "sqlite:///./nyaya_setu.db"  # convenient local/demo fallback
    secret_key: str
    access_token_expire_minutes: int = 45
    refresh_token_expire_days: int = 7
    cors_origins: str = "http://localhost:3000,http://localhost:5173"
    max_upload_bytes: int = 10 * 1024 * 1024
    rate_limit_per_minute: int = 60
    storage_root: Path = Path("storage")
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
