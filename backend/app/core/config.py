from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    data_dir: Path = Path("data")
    database_url: str = "sqlite:///./data/app.db"
    redis_url: str = "redis://localhost:6379/0"
    max_upload_bytes: int = 2 * 1024 * 1024 * 1024
    artifact_retention_hours: int = 72
    enable_startup_verification: bool = False
    run_jobs_inline: bool = True
    use_fixtures: bool = True
    curseforge_api_key: str | None = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()
