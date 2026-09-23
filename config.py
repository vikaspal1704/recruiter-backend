# config.py
"""Runtime settings read from the environment (see .env.example / docs/TRD.md)."""

import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()

__version__ = "0.1.0"

AUTH_MODES = ("api_key", "bearer", "api_key_or_bearer", "off")
DEFAULT_API_KEY_USER_ID = "00000000-0000-0000-0000-000000000000"


@dataclass(frozen=True)
class Settings:
    app_title: str
    app_env: str
    auth_mode: str
    api_key: str | None
    api_key_user_id: str
    cors_allow_origins: list[str]
    max_upload_bytes: int

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


def _load_settings() -> Settings:
    origins = os.getenv("CORS_ALLOW_ORIGINS", "http://localhost:3000,http://localhost:8000")
    settings = Settings(
        app_title=os.getenv("APP_TITLE", "Recruiter Talent Search API"),
        app_env=os.getenv("APP_ENV", "development"),
        auth_mode=os.getenv("AUTH_MODE", "api_key_or_bearer"),
        api_key=os.getenv("API_KEY") or None,
        api_key_user_id=os.getenv("API_KEY_USER_ID", DEFAULT_API_KEY_USER_ID),
        cors_allow_origins=[o.strip() for o in origins.split(",") if o.strip()],
        max_upload_bytes=int(os.getenv("MAX_UPLOAD_MB", "10")) * 1024 * 1024,
    )
    _validate(settings)
    return settings


def _validate(settings: Settings) -> None:
    if settings.auth_mode not in AUTH_MODES:
        raise RuntimeError(f"AUTH_MODE must be one of {AUTH_MODES}, got {settings.auth_mode!r}")
    if settings.auth_mode == "api_key" and not settings.api_key:
        raise RuntimeError("AUTH_MODE=api_key requires API_KEY to be set")
    if settings.is_production and settings.auth_mode == "off":
        raise RuntimeError("AUTH_MODE=off is not allowed when APP_ENV=production")
    if settings.is_production and "*" in settings.cors_allow_origins:
        raise RuntimeError("CORS_ALLOW_ORIGINS=* is not allowed when APP_ENV=production")


@lru_cache
def get_settings() -> Settings:
    return _load_settings()
