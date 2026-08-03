import json
from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


def _parse_cors_origins(raw: str) -> list[str]:
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return [origin.strip() for origin in raw.split(",") if origin.strip()]


class Settings(BaseSettings):
    """Configuraciones de la aplicacion cargadas desde las variables de entorno"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- App --------------------------------------------------------------------
    APP_NAME: str = "Financial Intelligence Platform"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"

    API_V1_PREFIX: str = "/api/v1"

    # --- Database ---------------------------------------------------------------
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/fip"
    DATABASE_ECHO: bool = False
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    DATABASE_POOL_PRE_PING: bool = True

    # --- Redis ------------------------------------------------------------------
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_MAX_CONNECTIONS: int = 20

    # --- Security ---------------------------------------------------------------
    SECRET_KEY: str = "CHANGE-ME-IN-PRODUCTION"  # noqa: S105
    ENCRYPTION_KEY: str = ""
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"

    # --- Email ------------------------------------------------------------------
    EMAIL_HOST: str = "smtp.gmail.com"
    EMAIL_PORT: int = 587
    EMAIL_USERNAME: str = ""
    EMAIL_PASSWORD: str = ""
    EMAIL_FROM: str = "noreply@fip.app"
    EMAIL_USE_TLS: bool = True

    # --- OAuth ------------------------------------------------------------------
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""

    # --- Notifications ---------------------------------------------------------
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_WEBHOOK_SECRET: str = ""
    DISCORD_WEBHOOK_URL: str = ""
    WEBHOOK_SECRET_KEY: str = ""
    NOTIFICATION_RETRY_ATTEMPTS: int = 3
    NOTIFICATION_RETRY_DELAY_SECONDS: int = 60
    ARQ_REDIS_URL: str = "redis://localhost:6379/0"

    # --- Frontend ---------------------------------------------------------------
    FRONTEND_URL: str = "http://localhost:3000"

    # --- MFA --------------------------------------------------------------------
    MFA_ISSUER_NAME: str = "FIP"

    # --- Rate Limit -------------------------------------------------------------
    # Coarse per-IP safety net (the fine-grained per-user limits live in
    # RATE_LIMIT_CONFIG in app/core/rate_limiter.py).
    RATE_LIMIT_MAX: int = 300
    RATE_LIMIT_WINDOW: int = 60

    # --- Idempotency ------------------------------------------------------------
    IDEMPOTENCY_KEY_TTL_SECONDS: int = 86400

    # --- Login Lockout ----------------------------------------------------------
    LOGIN_MAX_ATTEMPTS: int = 5
    LOGIN_LOCKOUT_MINUTES: int = 15

    # --- Multi-Currency ---------------------------------------------------------
    AUTO_CURRENCY_CONVERSION: bool = True
    EXCHANGE_RATE_API_URL: str = "https://api.exchangerate.host/convert"
    EXCHANGE_RATE_API_KEY: str = ""
    EXCHANGE_RATE_FETCH_TIMEOUT_SECONDS: float = 5.0
    EXCHANGE_RATE_NEAREST_LOOKBACK_DAYS: int = 30

    # --- CORS -------------------------------------------------------------------
    CORS_ORIGINS: str = '["http://localhost:3000","http://localhost:8000","http://localhost:8080","http://localhost:5173"]'

    @property
    def cors_origins_list(self) -> list[str]:
        return _parse_cors_origins(self.CORS_ORIGINS)

    # --- Monitoring -------------------------------------------------------------
    SENTRY_DSN: str = ""
    SENTRY_TRACES_SAMPLE_RATE: float = 0.1
    ENABLE_METRICS: bool = True
    ENABLE_TRACING: bool = True

    # --- LLM --------------------------------------------------------------------
    LLM_PROVIDER: str = "groq"
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "llama3-70b-8192"
    LLM_MAX_TOKENS: int = 512
    LLM_TEMPERATURE: float = 0.7
    LLM_TIMEOUT_SECONDS: int = 15

    # --- OpenTelemetry ----------------------------------------------------------
    OTEL_SERVICE_NAME: str = "fip-api"
    OTEL_EXPORTER_OTLP_ENDPOINT: str = "http://localhost:4317"

    # --- OCR --------------------------------------------------------------------
    # Si OCR_ENABLED=False o faltan los binarios de Tesseract/Poppler, el
    # endpoint degrada a extraccion por regex sobre el texto del archivo.
    OCR_ENABLED: bool = True
    TESSERACT_CMD: str = "tesseract"  # ruta binario tesseract (Windows: C:\Program Files\Tesseract-OCR\tesseract.exe)
    OCR_MAX_FILE_SIZE_MB: int = 10

    # --- Plaid ------------------------------------------------------------------
    # Sin credenciales los endpoints Plaid degradan con {enabled: False}.
    PLAID_ENABLED: bool = True
    PLAID_ENVIRONMENT: str = "sandbox"  # sandbox | development | production
    PLAID_CLIENT_ID: str = ""
    PLAID_SECRET: str = ""
    PLAID_REDIRECT_URI: str = ""

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def database_url_sync(self) -> str:
        "URL para alembic (sync driver)"
        return self.DATABASE_URL.replace("+asyncpg", "")

    @property
    def database_url_async(self) -> str:
        "URL for async engine (ensures +asyncpg driver)"
        url = self.DATABASE_URL
        if "+asyncpg" not in url and url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url


@lru_cache
def get_settings() -> Settings:
    """Cached singleton para ajustes."""
    return Settings()
