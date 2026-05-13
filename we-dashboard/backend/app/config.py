from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Core
    APP_NAME: str = "WE Quota Dashboard"
    DATABASE_URL: str = "sqlite+aiosqlite:////data/we.db"
    SECRET_KEY: str = "change-me-to-a-32-byte-random-string"
    ADMIN_PASSWORD: str = "change-me"
    JWT_ALGO: str = "HS256"
    JWT_TTL_HOURS: int = 168  # 7 days

    # WE Polling
    POLL_INTERVAL_MINUTES: int = 15

    # Alerts
    N8N_WEBHOOK_URL: str = ""  # Single global webhook for Telegram routing in n8n
    ALERT_THRESHOLDS: str = "80,90,95"  # CSV percentages; per-account override in DB

    # Bulk seed on first startup (accounts table empty)
    # Format: '[{"landline":"0212345678","password":"pass","label":"Home"},...]'
    # Set to empty string to skip.
    ACCOUNTS_SEED: str = ""

    # CORS
    ALLOWED_ORIGINS: str = "*"

    # Static frontend
    SERVE_FRONTEND: bool = True
    FRONTEND_DIST: str = "/app/frontend_dist"


@lru_cache
def get_settings() -> Settings:
    return Settings()
