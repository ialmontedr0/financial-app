"""Tests for the idempotency middleware."""

import json
import uuid

import pytest
from httpx import AsyncClient

from app.infrastructure.cache.redis import redis_client
from app.middleware.idempotency import IDEMPOTENCY_PREFIX, STATUS_PENDING


@pytest.mark.api
class TestIdempotency:
    """Idempotency-Key header must deduplicate mutating requests."""

    async def _register(self, client: AsyncClient, email: str, password: str) -> None:
        await client.post("/api/v1/auth/register", json={"email": email, "password": password})

    async def test_replay_returns_cached_response(
        self, client: AsyncClient, test_password: str
    ):
        email = "idem1@test.com"
        await self._register(client, email, test_password)
        key = str(uuid.uuid4())
        headers = {"Idempotency-Key": key}

        first = await client.post(
            "/api/v1/auth/login",
            headers=headers,
            json={"email": email, "password": test_password},
        )
        assert first.status_code == 200
        assert first.headers.get("Idempotency-Replay") == "false"
        assert first.headers.get("X-Idempotency-Key") == key

        replay = await client.post(
            "/api/v1/auth/login",
            headers=headers,
            json={"email": email, "password": test_password},
        )
        assert replay.status_code == 200
        assert replay.headers.get("Idempotency-Replay") == "true"
        assert replay.headers.get("X-Idempotency-Key") == key
        assert replay.json() == first.json()

    async def test_pending_key_returns_conflict(
        self, client: AsyncClient, test_password: str
    ):
        email = "idem2@test.com"
        await self._register(client, email, test_password)
        key = str(uuid.uuid4())
        await redis_client.set(
            f"{IDEMPOTENCY_PREFIX}:{key}",
            json.dumps({"status": STATUS_PENDING}),
        )

        response = await client.post(
            "/api/v1/auth/login",
            headers={"Idempotency-Key": key},
            json={"email": email, "password": test_password},
        )
        assert response.status_code == 409
        assert response.json()["error"]["code"] == "IDEMPOTENCY_PENDING"

    async def test_without_key_passes_through(
        self, client: AsyncClient, test_password: str
    ):
        email = "idem3@test.com"
        await self._register(client, email, test_password)

        response = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": test_password},
        )
        assert response.status_code == 200
        assert response.headers.get("Idempotency-Replay") is None

    async def test_read_methods_not_affected(self, client: AsyncClient):
        response = await client.get("/api/v1/health")
        assert response.status_code == 200
        assert response.headers.get("Idempotency-Replay") is None

    async def test_unique_keys_produce_independent_results(
        self, client: AsyncClient, test_password: str
    ):
        email = "idem4@test.com"
        await self._register(client, email, test_password)

        first = await client.post(
            "/api/v1/auth/login",
            headers={"Idempotency-Key": str(uuid.uuid4())},
            json={"email": email, "password": test_password},
        )
        second = await client.post(
            "/api/v1/auth/login",
            headers={"Idempotency-Key": str(uuid.uuid4())},
            json={"email": email, "password": test_password},
        )
        assert first.status_code == 200
        assert second.status_code == 200
        assert first.headers.get("Idempotency-Replay") == "false"
        assert second.headers.get("Idempotency-Replay") == "false"
        assert first.json()["tokens"]["access_token"] != second.json()["tokens"]["access_token"]
