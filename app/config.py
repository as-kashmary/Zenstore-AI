"""
Application configuration via environment variables.
Reads from a `.env` file when present.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    # ── App ──────────────────────────────────────────────
    APP_ENV: str = "development"
    SECRET_KEY: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── Database (MySQL via aiomysql) ────────────────────
    DATABASE_URL: str = "mysql+aiomysql://zenstore_user:zenstore_pass@localhost:3306/zenstore"

    # ── Redis ────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── Ollama (cloud) ──────────────────────────────
    OLLAMA_API_KEY: str = "your-ollama-api-key"

    # ── Cache ────────────────────────────────────────────
    LLM_CACHE_TTL_SECONDS: int = 86400


settings = Settings()