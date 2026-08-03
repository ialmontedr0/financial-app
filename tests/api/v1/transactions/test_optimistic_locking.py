"""Tests for optimistic locking (version field) on transaction updates."""

import pytest
from httpx import AsyncClient


@pytest.mark.api
class TestOptimisticLocking:
    """PATCH /transactions/{id} must reject stale versions with 409."""

    async def _setup(self, client: AsyncClient, email: str, test_password: str):
        await client.post("/api/v1/auth/register", json={"email": email, "password": test_password})
        login = await client.post("/api/v1/auth/login", json={"email": email, "password": test_password})
        token = login.json()["tokens"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        acc = await client.post(
            "/api/v1/accounts",
            headers=headers,
            json={"name": "Lock Acc", "account_type": "checking", "initial_balance": 50000},
        )
        acc_id = acc.json()["id"]
        tx = await client.post(
            "/api/v1/transactions",
            headers=headers,
            json={
                "account_id": acc_id,
                "transaction_type": "expense",
                "amount": 1000,
                "description": "Locked tx",
                "effective_date": "2026-07-19",
            },
        )
        return headers, tx.json()["id"]

    async def test_created_transaction_starts_at_version_one(
        self, client: AsyncClient, test_password: str
    ):
        headers, tx_id = await self._setup(client, "olock1@test.com", test_password)
        detail = await client.get(f"/api/v1/transactions/{tx_id}", headers=headers)
        assert detail.status_code == 200
        assert detail.json()["version"] == 1

    async def test_successful_update_increments_version(
        self, client: AsyncClient, test_password: str
    ):
        headers, tx_id = await self._setup(client, "olock2@test.com", test_password)

        response = await client.patch(
            f"/api/v1/transactions/{tx_id}",
            headers=headers,
            json={"description": "Updated desc", "version": 1},
        )
        assert response.status_code == 200
        assert response.json()["version"] == 2

    async def test_stale_version_rejected_with_conflict(
        self, client: AsyncClient, test_password: str
    ):
        headers, tx_id = await self._setup(client, "olock3@test.com", test_password)

        ok = await client.patch(
            f"/api/v1/transactions/{tx_id}",
            headers=headers,
            json={"description": "First edit", "version": 1},
        )
        assert ok.status_code == 200

        # A stale client still sends version=1 -> conflict
        stale = await client.patch(
            f"/api/v1/transactions/{tx_id}",
            headers=headers,
            json={"description": "Second edit", "version": 1},
        )
        assert stale.status_code == 409
        assert stale.json()["error"]["code"] == "CONFLICT"

    async def test_current_version_after_conflict_is_accepted(
        self, client: AsyncClient, test_password: str
    ):
        headers, tx_id = await self._setup(client, "olock4@test.com", test_password)

        first = await client.patch(
            f"/api/v1/transactions/{tx_id}",
            headers=headers,
            json={"description": "Edit A", "version": 1},
        )
        assert first.status_code == 200
        new_version = first.json()["version"]

        second = await client.patch(
            f"/api/v1/transactions/{tx_id}",
            headers=headers,
            json={"description": "Edit B", "version": new_version},
        )
        assert second.status_code == 200
        assert second.json()["version"] == new_version + 1
