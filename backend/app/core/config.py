"""
Centralized application configuration.

All environment-dependent values are read here ONCE via pydantic-settings.
Every other module should import `settings` from this file rather than
reading `os.environ` directly — this keeps configuration in one place and
makes the Supabase/Postgres migration a one-line change (DATABASE_URL).
"""
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ── App metadata ────────────────────────────────────────────────────
    APP_NAME: str = "Sparkle"
    ENVIRONMENT: str = "development"
    API_V1_PREFIX: str = "/api/v1"

    # ── Database ────────────────────────────────────────────────────────
    # SQLite locally by default. To move to Supabase/Postgres in production,
    # change ONLY this value (e.g. to
    # "postgresql+psycopg2://user:pass@host:5432/dbname").
    # No other code in the project references SQLite or Postgres directly.
    DATABASE_URL: str = "sqlite:///./jee_diagnosis.db"

    # ── Auth ────────────────────────────────────────────────────────────
    SECRET_KEY: str = "dev-only-secret-change-me"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # ── CORS ────────────────────────────────────────────────────────────
    FRONTEND_ORIGIN: str = "http://localhost:3000"

    # ── AI / Groq (wired up in Phase 3) ─────────────────────────────────
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    @property
    def cors_origins(self) -> List[str]:
        return [self.FRONTEND_ORIGIN, "http://127.0.0.1:3000"]

    @property
    def is_sqlite(self) -> bool:
        return self.DATABASE_URL.startswith("sqlite")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Cached settings accessor — avoids re-parsing the .env file per call."""
    return Settings()


settings = get_settings()
