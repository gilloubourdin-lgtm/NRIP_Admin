from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_NRIP_ROOT = PROJECT_ROOT.parent / "NRIP"


class Settings(BaseSettings):
    app_name: str = "NRIP Admin"
    app_version: str = "0.1.0"
    nrip_root: Path = DEFAULT_NRIP_ROOT

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="NRIP_ADMIN_",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.nrip_root = settings.nrip_root.expanduser().resolve()
    return settings