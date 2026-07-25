"""Rate limiting middleware using Redis sliding window."""

from __future__ import annotations

import time

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

from app.core.config import get_settings
from app.infrastructure.cache.redis import redis_client

settings = get_settings()


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, max_requests: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.url.path in ("/health", "/health/readiness", "/health/liveness", "/metrics"):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        window = int(time.time() / self.window_seconds)
        redis_key = f"ratelimit:{client_ip}:{window}"

        try:
            current = await redis_client.incr(redis_key)
            if current == 1:
                await redis_client.expire(redis_key, self.window_seconds)

            if current > self.max_requests:
                from fastapi.responses import JSONResponse

                return JSONResponse(
                    status_code=429,
                    content={
                        "success": False,
                        "error": {
                            "code": "RATE_LIMIT_EXCEEDED",
                            "message": f"Too many requests. Max {self.max_requests} per {self.window_seconds}s.",
                        },
                    },
                    headers={"Retry-After": str(self.window_seconds)},
                )
        except Exception:
            pass

        return await call_next(request)
