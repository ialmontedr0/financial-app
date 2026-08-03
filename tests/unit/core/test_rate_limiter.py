"""Unit tests for the per-user rate limiting dependency."""

from __future__ import annotations

from typing import Any

import pytest
from starlette.requests import Request

from app.core.rate_limiter import _resolve_identity, rate_limit
from app.infrastructure.rate_limit.rate_limit_service import RateLimitService
from app.middleware.error_handler import RateLimitError

TEST_USER_ID = "00000000-0000-0000-0000-000000000001"


def _make_request(*, token: str | None = None, user_id: str | None = None) -> Request:
    headers = [(b"host", b"test")]
    if token:
        headers.append((b"authorization", f"Bearer {token}".encode()))
    scope: dict[str, Any] = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": "/api/v1/transactions",
        "raw_path": b"/api/v1/transactions",
        "query_string": b"",
        "root_path": "",
        "headers": headers,
        "client": ("127.0.0.1", 50000),
        "server": ("test", 80),
        "app": {},
        "state": {},
    }
    request = Request(scope)
    if user_id:
        request.state.user_id = user_id
    return request


@pytest.mark.unit
class TestResolveIdentity:
    async def test_uses_request_state_user_id(self) -> None:
        request = _make_request(user_id="abc-123")
        assert _resolve_identity(request) == "user:abc-123"

    async def test_uses_bearer_token_sub(self, valid_access_token: str) -> None:
        request = _make_request(token=valid_access_token)
        assert _resolve_identity(request) == f"user:{TEST_USER_ID}"

    async def test_falls_back_to_client_ip(self) -> None:
        request = _make_request()
        assert _resolve_identity(request) == "ip:127.0.0.1"


@pytest.mark.unit
class TestRateLimitDependency:
    async def test_allows_request_within_limit(self, monkeypatch) -> None:
        async def fake_check(self, key: str, max_requests: int, window_seconds: int = 60):
            return True, 1, 0

        monkeypatch.setattr(RateLimitService, "check_rate_limit", fake_check)
        dep = rate_limit("auth")
        request = _make_request()

        result = await dep(request)
        assert result is None

    async def test_raises_when_limit_reached(self, monkeypatch) -> None:
        async def fake_check(self, key: str, max_requests: int, window_seconds: int = 60):
            return False, 6, 30

        monkeypatch.setattr(RateLimitService, "check_rate_limit", fake_check)
        dep = rate_limit("auth")
        request = _make_request()

        with pytest.raises(RateLimitError) as excinfo:
            await dep(request)
        assert excinfo.value.retry_after_seconds == 30
        assert excinfo.value.status_code == 429

    async def test_fails_open_on_redis_error(self, monkeypatch) -> None:
        async def boom(self, key: str, max_requests: int, window_seconds: int = 60):
            raise ConnectionError("redis down")

        monkeypatch.setattr(RateLimitService, "check_rate_limit", boom)
        dep = rate_limit("auth")
        request = _make_request()

        result = await dep(request)
        assert result is None
