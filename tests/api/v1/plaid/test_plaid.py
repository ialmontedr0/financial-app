"""Plaid API integration tests (graceful degradation sin credenciales)."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.api
class TestPlaidAPI:
    async def _register_and_login(self, client: AsyncClient, email: str, password: str) -> str:
        await client.post("/api/v1/auth/register", json={"email": email, "password": password})
        login_resp = await client.post(
            "/api/v1/auth/login", json={"email": email, "password": password}
        )
        return login_resp.json()["tokens"]["access_token"]

    async def test_status_degraded(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "pl_status@test.com", test_password)
        resp = await client.get(
            "/api/v1/plaid/status", headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["enabled"] is False
        assert data["environment"] == "sandbox"

    async def test_link_token_degraded(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "pl_link@test.com", test_password)
        resp = await client.post(
            "/api/v1/plaid/link-token",
            json={},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is False
        assert data["enabled"] is False
        assert data["link_token"] is None

    async def test_exchange_token_degraded(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "pl_exc@test.com", test_password)
        resp = await client.post(
            "/api/v1/plaid/exchange-token",
            json={"public_token": "public-sandbox-0000"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is False
        assert data["enabled"] is False
        assert data["item"] is None

    async def test_exchange_token_missing(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "pl_exc2@test.com", test_password)
        resp = await client.post(
            "/api/v1/plaid/exchange-token",
            json={},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422

    async def test_list_items_empty(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "pl_items@test.com", test_password)
        resp = await client.get("/api/v1/plaid/items", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert resp.json() == {"items": []}
