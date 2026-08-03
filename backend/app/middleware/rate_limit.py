"""Rate limiting middleware using Redis sliding window (per IP)."""

from __future__ import annotations

import structlog
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

from app.core.config import get_settings
from app.infrastructure.cache.redis import redis_client
from app.infrastructure.rate_limit.rate_limit_service import RateLimitService

settings = get_settings()

logger = structlog.get_logger()

_SKIP_PATHS = {"/health", "/health/readiness", "/health/liveness", "/metrics"}


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Per-IP safety net using the same sliding-window service as the per-user limiter."""

    def __init__(self, app: ASGIApp, max_requests: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._service = RateLimitService(redis_client)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.url.path in _SKIP_PATHS:
            return await call_next(request)

        identity = request.client.host if request.client else "unknown"
        key = RateLimitService.build_key("ip", identity)

        try:
            allowed, _, retry_after = await self._service.check_rate_limit(
                key, self.max_requests, self.window_seconds
            )
            if not allowed:
                logger.warning(
                    "rate_limit_exceeded_ip",
                    identity=identity,
                    limit=self.max_requests,
                    retry_after=retry_after,
                )
                return JSONResponse(
                    status_code=429,
                    content={
                        "success": False,
                        "error": {
                            "code": "RATE_LIMIT_EXCEEDED",
                            "message": (
                                f"Too many requests. Max {self.max_requests} per "
                                f"{self.window_seconds}s."
                            ),
                        },
                    },
                    headers={"Retry-After": str(retry_after)},
                )
        except Exception:
            logger.warning("rate_limit_redis_error", exc_info=True)

        return await call_next(request)
