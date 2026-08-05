"""API tests for full-text search."""

import pytest
from httpx import AsyncClient


@pytest.mark.api
class TestSearch:
    async def _setup(self, client: AsyncClient, email: str, password: str) -> str:
        await client.post("/api/v1/auth/register", json={"email": email, "password": password})
        login = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
        return login.json()["tokens"]["access_token"]

    async def _create_account(self, client: AsyncClient, token: str) -> str:
        resp = await client.post(
            "/api/v1/accounts",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Search Account", "account_type": "checking", "initial_balance": 50000},
        )
        return resp.json()["id"]

    async def _create_transaction(
        self, client: AsyncClient, token: str, account_id: str, description: str
    ) -> None:
        await client.post(
            "/api/v1/transactions",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "account_id": account_id,
                "transaction_type": "expense",
                "amount": 1500.50,
                "description": description,
                "effective_date": "2026-07-19",
            },
        )

    async def test_search_transactions_empty(self, client: AsyncClient, test_password: str):
        token = await self._setup(client, "search1@test.com", test_password)
        headers = {"Authorization": f"Bearer {token}"}
        resp = await client.get("/api/v1/search/transactions", headers=headers, params={"q": "xyz"})
        assert resp.status_code == 200
        assert resp.json()["total"] == 0
        assert resp.json()["results"] == []

    async def test_search_transactions_finds_match(self, client: AsyncClient, test_password: str):
        token = await self._setup(client, "search2@test.com", test_password)
        headers = {"Authorization": f"Bearer {token}"}
        acc_id = await self._create_account(client, token)
        await self._create_transaction(client, token, acc_id, "Supermercado La Colonia")
        await self._create_transaction(client, token, acc_id, "Farmacia Cruz Verde")

        resp = await client.get("/api/v1/search/transactions", headers=headers, params={"q": "supermercado"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["results"][0]["description"] == "Supermercado La Colonia"

    async def test_search_isolated_per_user(self, client: AsyncClient, test_password: str):
        token_a = await self._setup(client, "search3@test.com", test_password)
        token_b = await self._setup(client, "search4@test.com", test_password)
        acc_a = await self._create_account(client, token_a)
        await self._create_transaction(client, token_a, acc_a, "Pago Netflix")

        resp_a = await client.get(
            "/api/v1/search/transactions", headers={"Authorization": f"Bearer {token_a}"}, params={"q": "netflix"}
        )
        assert resp_a.json()["total"] == 1

        resp_b = await client.get(
            "/api/v1/search/transactions", headers={"Authorization": f"Bearer {token_b}"}, params={"q": "netflix"}
        )
        assert resp_b.json()["total"] == 0

    async def test_search_suggestions(self, client: AsyncClient, test_password: str):
        token = await self._setup(client, "search5@test.com", test_password)
        headers = {"Authorization": f"Bearer {token}"}
        resp = await client.get("/api/v1/search/suggestions", headers=headers, params={"q": "ab"})
        assert resp.status_code == 200
        assert "suggestions" in resp.json()
        assert isinstance(resp.json()["suggestions"], list)

    async def test_search_requires_min_length(self, client: AsyncClient, test_password: str):
        token = await self._setup(client, "search6@test.com", test_password)
        headers = {"Authorization": f"Bearer {token}"}
        resp = await client.get("/api/v1/search/transactions", headers=headers, params={"q": "x"})
        assert resp.status_code == 422

    async def test_search_requires_auth(self, client: AsyncClient):
        resp = await client.get(
            "/api/v1/search/transactions",
            params={"q": "netflix"},
            headers={"Authorization": "Bearer invalid.token.value"},
        )
        assert resp.status_code == 401
