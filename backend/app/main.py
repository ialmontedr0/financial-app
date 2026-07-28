from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import sentry_sdk
import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

print("DEBUG 1: imports done", flush=True)

from app.api.v1.router import api_v1_router
print("DEBUG 2: router imported", flush=True)
from app.core.config import get_settings

print("DEBUG 3: config imported", flush=True)
from app.middleware.error_handler import register_error_handlers
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.request_logger import RequestLoggingMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware

print("DEBUG 4: middleware imported", flush=True)

settings = get_settings()
print("DEBUG 5: settings loaded", flush=True)
logger = structlog.get_logger()


def configure_sentry() -> None:
    """Inicializar sentry si DSN es proveido"""
    if settings.SENTRY_DSN:
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            environment=settings.ENVIRONMENT,
            traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
            send_default_pii=True,
        )
        logger.info("Sentry inicializado", environment=settings.ENVIRONMENT)


def configure_prometheus(app: FastAPI) -> None:
    if settings.ENABLE_METRICS:
        from prometheus_fastapi_instrumentator import Instrumentator

        Instrumentator(
            should_group_status_codes=False,
            excluded_handlers=["/metrics", "/health"],
            env_var_name="ENABLE_METRICS",
        ).instrument(app).expose(app)
        logger.info("Prometheus metrics enabled")


def configure_opentelemetry(app: FastAPI) -> None:
    if settings.ENABLE_TRACING:
        from app.infrastructure.monitoring.tracking import setup_tracking

        setup_tracking(app)
        logger.info("OpenTelemetry tracking enabled")


def _check_production_env() -> None:
    """Verify critical env vars are set in production."""
    required = ["DATABASE_URL", "REDIS_URL", "SECRET_KEY", "ENCRYPTION_KEY"]
    missing = [var for var in required if not getattr(settings, var, None)]
    if missing:
        logger.error("Missing required env vars in production", missing=missing)
        msg = f"Missing required environment variables: {', '.join(missing)}"
        raise RuntimeError(msg)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:  # noqa: UP043
    """Ciclo de vida de la aplicacion: eventos de inicio y apagado"""
    # --- INICIO ---
    if settings.is_production:
        _check_production_env()
        from app.core.log_config import configure_production_logging
        configure_production_logging()

    logger.info("Iniciando API FIP", version=settings.APP_VERSION)
    configure_sentry()

    # Seed system categories on startup
    from app.infrastructure.db.session import async_session_factory
    from app.infrastructure.seed.category_seed import seed_system_categories
    from app.infrastructure.seed.role_seed import seed_roles_and_permissions

    async with async_session_factory() as session, session.begin():
        await seed_system_categories(session)
        await seed_roles_and_permissions(session)

    yield

    # --- APAGADO ---
    logger.info("Apagando API FIP")


def create_app() -> FastAPI:
    """Aplicacion por defecto."""
    print("DEBUG 6: starting create_app", flush=True)
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        openapi_url="/openapi.json" if not settings.is_production else None,
        lifespan=lifespan,
    )
    print("DEBUG 7: FastAPI created", flush=True)

    # --- Middleware (must be added before startup) -----------------------------
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(SecurityHeadersMiddleware)
    print("DEBUG 8: CORS + Security middleware added", flush=True)
    app.add_middleware(RateLimitMiddleware, max_requests=settings.RATE_LIMIT_MAX, window_seconds=settings.RATE_LIMIT_WINDOW)
    app.add_middleware(RequestLoggingMiddleware)
    print("DEBUG 9: rate limit + request logging added", flush=True)

    # --- Monitoring (middleware must be added before startup) ------------------
    configure_prometheus(app)
    print("DEBUG 10: prometheus configured", flush=True)
    configure_opentelemetry(app)
    print("DEBUG 11: opentelemetry configured", flush=True)

    # --- Error handlers --------------------------------------------------------
    register_error_handlers(app)
    print("DEBUG 12: error handlers registered", flush=True)

    # --- Routers ---------------------------------------------------------------
    app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)
    print("DEBUG 13: router included", flush=True)

    # --- Health Check ----------------------------------------------------------
    from app.api.v1.health.router import router as health_router
    app.include_router(health_router)
    print("DEBUG 14: health router included", flush=True)

    return app


# Punto de entrada para uvicorn
print("DEBUG 0: before create_app()", flush=True)
app = create_app()
print("DEBUG 15: app created", flush=True)
