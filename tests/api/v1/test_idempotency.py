"""Tests for idempotency middleware.

Verifies:
- GET/DELETE pass through without idempotency behavior.
- POST without Idempotency-Key passes through.
- First POST with key returns 201 and stores response.
- Second POST with same key returns replayed response (Idempotency-Replay: true).
- Concurrent POST with same key returns 409 while first is in-flight.
- After Redis flush, BD fallback returns the stored completed response.
"""

import json
import uuid

import pytest
import redis.asyncio as aioredis
from httpx import AsyncClient

from app.core.config import get_settings
from app.infrastructure.cache.redis import redis_client
from app.infrastructure.db.session import async_session_factory
from app.infrastructure.repositories.idempotency_repository import IdempotencyRepository

settings = get_settings()
IDEMPOTENCY_PREFIX = "fip:idempotency:"


@pytest.fixture(autouse=True)
async def _clean_idempotency_keys():
    """Flush all idempotency keys from Redis before and after each test.

    Uses a fresh connection to avoid event-loop attachment issues with the
    module-level ``redis_client`` singleton.
    """
    tmp = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    try:
        keys = await tmp.keys(f"{IDEMPOTENCY_PREFIX}*")
        if keys:
            await tmp.delete(*keys)
        yield
        keys = await tmp.keys(f"{IDEMPOTENCY_PREFIX}*")
        if keys:
            await tmp.delete(*keys)
    finally:
        await tmp.aclose()


def _unique_key(prefix: str = "test") -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


@pytest.mark.api
class TestIdempotencyPassThrough:
    """Endpoints that should NOT be affected by idempotency middleware."""

    async def _register_and_login(self, client: AsyncClient, email: str, password: str) -> str:
        await client.post("/api/v1/auth/register", json={"email": email, "password": password})
        login_resp = await client.post(
            "/api/v1/auth/login", json={"email": email, "password": password}
        )
        return login_resp.json()["tokens"]["access_token"]

    async def test_get_bypasses_idempotency(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "idem_get@test.com", test_password)
        resp = await client.get(
            "/api/v1/accounts",
            headers={"Authorization": f"Bearer {token}", "Idempotency-Key": _unique_key("get")},
        )
        assert resp.status_code == 200
        assert resp.headers.get("Idempotency-Replay") is None

    async def test_post_without_key_bypasses(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "idem_nokey@test.com", test_password)
        resp = await client.post(
            "/api/v1/accounts",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "No Key Account", "account_type": "checking"},
        )
        assert resp.status_code == 201
        assert resp.headers.get("Idempotency-Replay") is None


@pytest.mark.api
class TestIdempotencyReplay:
    """Core idempotency: first request stores, second replays."""

    async def _register_and_login(self, client: AsyncClient, email: str, password: str) -> str:
        await client.post("/api/v1/auth/register", json={"email": email, "password": password})
        login_resp = await client.post(
            "/api/v1/auth/login", json={"email": email, "password": password}
        )
        return login_resp.json()["tokens"]["access_token"]

    async def test_first_request_stores_and_returns_201(
        self, client: AsyncClient, test_password: str
    ):
        token = await self._register_and_login(client, "idem_first@test.com", test_password)
        key = _unique_key("first")
        resp = await client.post(
            "/api/v1/accounts",
            headers={"Authorization": f"Bearer {token}", "Idempotency-Key": key},
            json={"name": "Idem Account", "account_type": "checking"},
        )
        assert resp.status_code == 201
        assert resp.headers.get("Idempotency-Replay") == "false"
        assert resp.headers.get("X-Idempotency-Key") == key

        # Verify stored in Redis
        redis_key = f"fip:idempotency:{key}"
        cached = await redis_client.get(redis_key)
        assert cached is not None
        record = json.loads(cached)
        assert record["status"] == "completed"
        assert record["status_code"] == 201

    async def test_second_request_replays(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "idem_replay@test.com", test_password)
        key = _unique_key("replay")

        # First request
        resp1 = await client.post(
            "/api/v1/accounts",
            headers={"Authorization": f"Bearer {token}", "Idempotency-Key": key},
            json={"name": "Replay Account", "account_type": "bank"},
        )
        assert resp1.status_code == 201
        first_id = resp1.json()["id"]

        # Second request — should replay
        resp2 = await client.post(
            "/api/v1/accounts",
            headers={"Authorization": f"Bearer {token}", "Idempotency-Key": key},
            json={"name": "Replay Account", "account_type": "bank"},
        )
        assert resp2.status_code == 201
        assert resp2.headers.get("Idempotency-Replay") == "true"
        assert resp2.json()["id"] == first_id

    async def test_same_key_produces_same_account_not_duplicate(
        self, client: AsyncClient, test_password: str
    ):
        token = await self._register_and_login(client, "idem_dedup@test.com", test_password)
        key = _unique_key("dedup")

        await client.post(
            "/api/v1/accounts",
            headers={"Authorization": f"Bearer {token}", "Idempotency-Key": key},
            json={"name": "Dedup Account", "account_type": "checking"},
        )
        await client.post(
            "/api/v1/accounts",
            headers={"Authorization": f"Bearer {token}", "Idempotency-Key": key},
            json={"name": "Dedup Account", "account_type": "checking"},
        )

        resp = await client.get(
            "/api/v1/accounts",
            headers={"Authorization": f"Bearer {token}"},
        )
        accounts = [a for a in resp.json()["accounts"] if a["name"] == "Dedup Account"]
        assert len(accounts) == 1


@pytest.mark.api
class TestIdempotencyConcurrent:
    """Concurrent requests with same key while first is in-flight."""

    async def _register_and_login(self, client: AsyncClient, email: str, password: str) -> str:
        await client.post("/api/v1/auth/register", json={"email": email, "password": password})
        login_resp = await client.post(
            "/api/v1/auth/login", json={"email": email, "password": password}
        )
        return login_resp.json()["tokens"]["access_token"]

    async def test_second_concurrent_returns_409(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "idem_conc@test.com", test_password)
        key = _unique_key("conc")
        redis_key = f"fip:idempotency:{key}"

        # Manually set pending state in Redis (simulates first request in-flight)
        await redis_client.set(
            redis_key,
            json.dumps({"status": "pending"}),
            nx=True,
            ex=86400,
        )

        resp = await client.post(
            "/api/v1/accounts",
            headers={"Authorization": f"Bearer {token}", "Idempotency-Key": key},
            json={"name": "Should Conflict", "account_type": "checking"},
        )
        assert resp.status_code == 409
        data = resp.json()
        assert data["error"]["code"] == "IDEMPOTENCY_PENDING"


@pytest.mark.api
class TestIdempotencyDBFallback:
    """After Redis flush, BD fallback returns the stored completed response."""

    async def _register_and_login(self, client: AsyncClient, email: str, password: str) -> str:
        await client.post("/api/v1/auth/register", json={"email": email, "password": password})
        login_resp = await client.post(
            "/api/v1/auth/login", json={"email": email, "password": password}
        )
        return login_resp.json()["tokens"]["access_token"]

    async def test_bd_fallback_after_redis_flush(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "idem_fallback@test.com", test_password)
        key = _unique_key("fallback")
        redis_key = f"fip:idempotency:{key}"

        # First request — stores in both Redis and BD
        resp1 = await client.post(
            "/api/v1/accounts",
            headers={"Authorization": f"Bearer {token}", "Idempotency-Key": key},
            json={"name": "Fallback Account", "account_type": "checking"},
        )
        assert resp1.status_code == 201
        first_id = resp1.json()["id"]

        # Verify BD record exists
        async with async_session_factory() as session:  # noqa: SIM117
            async with session.begin():
                repo = IdempotencyRepository(session)
                db_record = await repo.get(key)
                assert db_record is not None
                assert db_record.status == "completed"
                assert db_record.status_code == 201

        # Flush Redis key (simulates Redis restart)
        await redis_client.delete(redis_key)

        # Second request — should fallback to BD and replay
        resp2 = await client.post(
            "/api/v1/accounts",
            headers={"Authorization": f"Bearer {token}", "Idempotency-Key": key},
            json={"name": "Fallback Account", "account_type": "checking"},
        )
        assert resp2.status_code == 201
        assert resp2.headers.get("Idempotency-Replay") == "true"
        assert resp2.json()["id"] == first_id

    async def test_bd_pending_returns_409(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "idem_pend@test.com", test_password)
        key = _unique_key("pend")

        # Insert a pending record directly in BD
        async with async_session_factory() as session:  # noqa: SIM117
            async with session.begin():
                repo = IdempotencyRepository(session)
                await repo.create(key=key, method="POST", path="/api/v1/accounts")

        # Flush Redis to force BD fallback path
        await redis_client.delete(f"fip:idempotency:{key}")

        resp = await client.post(
            "/api/v1/accounts",
            headers={"Authorization": f"Bearer {token}", "Idempotency-Key": key},
            json={"name": "Should Conflict BD", "account_type": "checking"},
        )
        assert resp.status_code == 409
        assert resp.json()["error"]["code"] == "IDEMPOTENCY_PENDING"
