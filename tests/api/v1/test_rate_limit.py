"""API tests for per-user rate limiting (429 responses)."""

import uuid

import pytest
from httpx import AsyncClient

from app.infrastructure.models.user import UserModel
from app.infrastructure.rate_limit.rate_limit_service import RateLimitService

TEST_USER_ID = "00000000-0000-0000-0000-000000000001"


@pytest.mark.api
class TestRateLimitApi:
    async def test_rate_limited_endpoint_returns_429(
        self, client: AsyncClient, monkeypatch
    ) -> None:
        real_check = RateLimitService.check_rate_limit

        async def fake_check(self, key: str, max_requests: int, window_seconds: int = 60):
            if key.startswith("ratelimit:auth:ip:"):
                return False, 6, 30
            return await real_check(self, key, max_requests, window_seconds)

        monkeypatch.setattr(RateLimitService, "check_rate_limit", fake_check)

        response = await client.post(
            "/api/v1/auth/request-email-verification",
            json={"email": "ratelimit@example.com"},
        )

        assert response.status_code == 429
        body = response.json()
        assert body["success"] is False
        assert body["error"]["code"] == "RATE_LIMIT_EXCEEDED"
        assert response.headers.get("retry-after") == "30"

    async def test_rate_limited_endpoint_allows_request(
        self, client: AsyncClient, monkeypatch
    ) -> None:
        async def fake_check(self, key: str, max_requests: int, window_seconds: int = 60):
            return True, 1, 0

        monkeypatch.setattr(RateLimitService, "check_rate_limit", fake_check)

        response = await client.post(
            "/api/v1/auth/request-email-verification",
            json={"email": "ratelimit-ok@example.com"},
        )

        assert response.status_code == 200

    async def test_blocks_by_user_id_not_ip(
        self, client: AsyncClient, db_session, monkeypatch, valid_access_token: str
    ) -> None:
        user = UserModel(
            id=uuid.UUID(TEST_USER_ID),
            email="ratelimit-user@example.com",
            password_hash=f"hashed-{uuid.uuid4().hex}",
        )
        db_session.add(user)
        await db_session.commit()

        real_check = RateLimitService.check_rate_limit

        async def fake_check(self, key: str, max_requests: int, window_seconds: int = 60):
            if key.startswith(f"ratelimit:auth:user:{TEST_USER_ID}"):
                return False, 6, 30
            return await real_check(self, key, max_requests, window_seconds)

        monkeypatch.setattr(RateLimitService, "check_rate_limit", fake_check)

        response = await client.post(
            "/api/v1/auth/mfa/enable",
            headers={"Authorization": f"Bearer {valid_access_token}"},
        )

        assert response.status_code == 429
        assert response.json()["error"]["code"] == "RATE_LIMIT_EXCEEDED"

        await db_session.delete(user)
        await db_session.commit()
