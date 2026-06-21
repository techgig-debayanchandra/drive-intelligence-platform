"""Application settings and configuration loading."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """Runtime configuration for the platform."""

    model_config = SettingsConfigDict(env_prefix="DIP_", env_file=".env", extra="ignore")

    app_name: str = "Drive Intelligence Platform"
    environment: str = "development"
    database_url: str = Field(default="sqlite:///data/drive_intelligence.sqlite3")
    mode: str = Field(default="read_only")
    data_root: Path = Field(default=Path("data"))
    log_level: str = Field(default="INFO")
    max_workers: int = 8
    batch_size: int = 1000
    similarity_threshold: float = 0.92
    openai_api_key: str | None = None
    openai_model: str = "gpt-4.1-mini"
    ui_bootstrap_cdn: bool = True
    ui_max_table_rows: int = 500


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    """Return cached application settings."""

    settings = AppSettings()
    settings.data_root.mkdir(parents=True, exist_ok=True)
    return settings