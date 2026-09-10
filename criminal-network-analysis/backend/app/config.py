"""
Centralized application settings.

All configuration is read from environment variables (see .env.example).
Nothing here is a real secret -- the defaults are safe placeholders for a
local demo only and must be overridden before any real deployment.
"""
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(BACKEND_DIR / ".env"), extra="ignore")

    app_name: str = "AI-Powered Criminal Network Analysis System"
    environment: str = "development"
    debug: bool = True

    database_url: str = f"sqlite:///{(BACKEND_DIR / 'crime_network.db').as_posix()}"

    jwt_secret_key: str = "change-this-to-a-long-random-string-before-any-real-deployment"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    cors_origins: str = "http://localhost:5180,http://127.0.0.1:5180,http://localhost:5173,http://127.0.0.1:5173"

    rate_limit_per_minute: int = 120

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
