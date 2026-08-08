"""Per-user rate limiting dependency.

A FastAPI dependency factory that limits requests per identity (authenticated
user id, falling back to the client IP for anonymous requests). The window is
a sliding window enforced with a Redis sorted set.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

import structlog
from fastapi import Request

from app.infrastructure.cache.redis import redis_client
from app.infrastructure.rate_limit.rate_limit_service import RateLimitService
from app.middleware.error_handler import RateLimitError

logger = structlog.get_logger()

# Default requests per minute per scope.
RATE_LIMIT_CONFIG: dict[str, int] = {
    "auth": 5,
    "analytics": 30,
    "default": 60,
}


def _resolve_identity(request: Request) -> str:
    """Identify the caller: authenticated user id when available, else IP."""
    user_id = getattr(request.state, "user_id", None)
    if user_id:
        return f"user:{user_id}"

    authorization = request.headers.get("authorization", "")
    if authorization.startswith("Bearer "):
        from app.infrastructure.security.jwt_service import JWTService

        payload = JWTService.verify_token(authorization[7:], expected_type="access")
        if payload and payload.get("sub"):
            return f"user:{payload['sub']}"

    host = request.client.host if request.client else "unknown"
    return f"ip:{host}"


def rate_limit(
    scope: str = "default",
    max_requests: int | None = None,
    window_seconds: int = 60,
) -> Callable[[Request], Awaitable[None]]:
    """Return a FastAPI dependency enforcing a per-identity rate limit.

    The dependency fails open: if Redis is unavailable the request is allowed
    through (a warning is logged) so the rate limiter never breaks the API.
    """
    limit = max_requests or RATE_LIMIT_CONFIG.get(scope, RATE_LIMIT_CONFIG["default"])

    async def _check(request: Request) -> None:
        identity = _resolve_identity(request)
        key = RateLimitService.build_key(scope, identity)
        try:
            service = RateLimitService(redis_client)
            allowed, count, retry_after = await service.check_rate_limit(key, limit, window_seconds)
        except Exception:
            logger.warning("rate_limit_redis_error", scope=scope, exc_info=True)
            return

        if not allowed:
            logger.warning(
                "rate_limit_exceeded",
                scope=scope,
                identity=identity,
                count=count,
                limit=limit,
            )
            raise RateLimitError(retry_after_seconds=retry_after)

    return _check


def login_rate_limit(
    scope: str = "login",
    max_requests: int = 10,
    window_seconds: int = 60,
) -> Callable[[Request], Awaitable[None]]:
    """Rate limit por email (antes de autenticar) en login.

    Previene fuerza bruta dirigida a una cuenta concreta además del límite
    global por IP que aplica el middleware.
    """
    import json

    async def _check(request: Request) -> None:
        raw_body = await request.body()
        identity = "unknown"
        try:
            payload = json.loads(raw_body or b"{}")
            email = str(payload.get("email", "")).strip().lower()
            if email:
                identity = f"email:{email}"
        except (ValueError, TypeError):
            pass

        key = RateLimitService.build_key(scope, identity)
        try:
            service = RateLimitService(redis_client)
            allowed, count, retry_after = await service.check_rate_limit(key, max_requests, window_seconds)
        except Exception:
            logger.warning("rate_limit_redis_error", scope=scope, exc_info=True)
            return

        if not allowed:
            logger.warning(
                "rate_limit_exceeded_login",
                identity=identity,
                count=count,
                limit=max_requests,
            )
            raise RateLimitError(retry_after_seconds=retry_after)

    return _check


def get_rate_limit_config() -> dict[str, Any]:
    """Expose the scope configuration (useful for admin/ops tooling)."""
    return dict(RATE_LIMIT_CONFIG)
