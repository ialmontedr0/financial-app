"""Tests for optimistic locking on financial accounts.

Verifies:
- Update without version field always succeeds (no conflict check).
- Update with correct version succeeds and increments version.
- Update with stale version returns 409 CONFLICT.
- After conflict, the client can re-read and retry with the new version.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.api
class TestOptimisticLocking:
    """Optimistic locking via version column on FinancialAccountModel."""

    async def _register_and_login(self, client: AsyncClient, email: str, password: str) -> str:
        await client.post("/api/v1/auth/register", json={"email": email, "password": password})
        login_resp = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
        return login_resp.json()["tokens"]["access_token"]

    async def _create_account(self, client: AsyncClient, token: str) -> dict:
        resp = await client.post(
            "/api/v1/accounts",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Version Test", "account_type": "checking", "currency_code": "DOP"},
        )
        return resp.json()

    async def test_update_without_version_always_succeeds(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "noversion@test.com", test_password)
        acc = await self._create_account(client, token)

        resp = await client.patch(
            f"/api/v1/accounts/{acc['id']}",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Updated No Version"},
        )
        assert resp.status_code == 200

        get_resp = await client.get(
            f"/api/v1/accounts/{acc['id']}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert get_resp.json()["name"] == "Updated No Version"

    async def test_update_with_correct_version_succeeds(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "correctver@test.com", test_password)
        acc = await self._create_account(client, token)
        initial_version = acc["version"]
        assert initial_version == 1

        resp = await client.patch(
            f"/api/v1/accounts/{acc['id']}",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Updated Correct", "version": initial_version},
        )
        assert resp.status_code == 200
        assert resp.json()["version"] == initial_version + 1

    async def test_update_with_stale_version_returns_409(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "stalever@test.com", test_password)
        acc = await self._create_account(client, token)
        stale_version = acc["version"]  # version 1

        # First update succeeds — version becomes 2
        resp1 = await client.patch(
            f"/api/v1/accounts/{acc['id']}",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "First Update", "version": stale_version},
        )
        assert resp1.status_code == 200

        # Second update with stale version 1 — should fail
        resp2 = await client.patch(
            f"/api/v1/accounts/{acc['id']}",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Stale Update", "version": stale_version},
        )
        assert resp2.status_code == 409
        data = resp2.json()
        assert data["error"]["code"] == "CONFLICT"
        assert "otro usuario" in data["error"]["message"]

    async def test_after_conflict_re_read_and_retry_succeeds(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "retry@test.com", test_password)
        acc = await self._create_account(client, token)

        # Simulate concurrent edit: another user updates
        resp1 = await client.patch(
            f"/api/v1/accounts/{acc['id']}",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Concurrent Edit", "version": acc["version"]},
        )
        assert resp1.status_code == 200

        # Client re-reads to get fresh version
        fresh = await client.get(
            f"/api/v1/accounts/{acc['id']}",
            headers={"Authorization": f"Bearer {token}"},
        )
        fresh_version = fresh.json()["version"]
        assert fresh_version == 2

        # Retry with correct version
        resp2 = await client.patch(
            f"/api/v1/accounts/{acc['id']}",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Retry Success", "version": fresh_version},
        )
        assert resp2.status_code == 200
        assert resp2.json()["version"] == 3

    async def test_version_increments_on_each_update(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "increment@test.com", test_password)
        acc = await self._create_account(client, token)

        for i in range(5):
            # Re-read current version
            current = await client.get(
                f"/api/v1/accounts/{acc['id']}",
                headers={"Authorization": f"Bearer {token}"},
            )
            current_version = current.json()["version"]

            resp = await client.patch(
                f"/api/v1/accounts/{acc['id']}",
                headers={"Authorization": f"Bearer {token}"},
                json={"name": f"Update {i + 1}", "version": current_version},
            )
            assert resp.status_code == 200
            assert resp.json()["version"] == current_version + 1
