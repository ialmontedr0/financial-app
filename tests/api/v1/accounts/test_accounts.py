"""Tests for financial account endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.api
class TestCreateAccount:
    """Tests for POST /accounts."""

    async def _register_and_login(self, client: AsyncClient, email: str, password: str) -> str:
        """Helper: register user, login, return access token."""
        await client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": password},
        )
        login_resp = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
        )
        return login_resp.json()["tokens"]["access_token"]

    async def test_create_bank_account(self, client: AsyncClient, test_password: str):
        email = "accounts@test.com"
        token = await self._register_and_login(client, email, test_password)
        response = await client.post(
            "/api/v1/accounts",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "Banco Popular",
                "account_type": "bank",
                "currency_code": "DOP",
                "initial_balance": 50000.00,
                "institution": "Banco Popular Dominicano",
                "account_number_last4": "1234",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Banco Popular"
        assert data["account_type"] == "bank"
        assert data["currency_code"] == "DOP"
        assert data["balance"] == "50000.0"
        assert data["status"] == "active"

    async def test_create_cash_account(self, client: AsyncClient, test_password: str):
        email = "cash@test.com"
        token = await self._register_and_login(client, email, test_password)
        response = await client.post(
            "/api/v1/accounts",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "Efectivo",
                "account_type": "cash",
                "currency_code": "DOP",
                "initial_balance": 5000.00,
            },
        )
        assert response.status_code == 201
        assert response.json()["account_type"] == "cash"

    async def test_create_crypto_account(self, client: AsyncClient, test_password: str):
        email = "crypto@test.com"
        token = await self._register_and_login(client, email, test_password)
        response = await client.post(
            "/api/v1/accounts",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "Binance BTC",
                "account_type": "crypto",
                "currency_code": "USD",
                "initial_balance": 0.05,
                "institution": "Binance",
            },
        )
        assert response.status_code == 201
        assert response.json()["account_type"] == "crypto"

    async def test_create_account_missing_type(self, client: AsyncClient, test_password: str):
        email = "notype@test.com"
        token = await self._register_and_login(client, email, test_password)
        response = await client.post(
            "/api/v1/accounts",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Test"},
        )
        assert response.status_code == 422

    async def test_create_account_invalid_type(self, client: AsyncClient, test_password: str):
        email = "badtype@test.com"
        token = await self._register_and_login(client, email, test_password)
        response = await client.post(
            "/api/v1/accounts",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Test", "account_type": "invalid"},
        )
        assert response.status_code == 422

    async def test_create_account_invalid_currency(self, client: AsyncClient, test_password: str):
        email = "badcurr@test.com"
        token = await self._register_and_login(client, email, test_password)
        response = await client.post(
            "/api/v1/accounts",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Test", "account_type": "bank", "currency_code": "XYZ"},
        )
        assert response.status_code == 422


@pytest.mark.api
class TestListAccounts:
    """Tests for GET /accounts."""

    async def _register_and_login(self, client: AsyncClient, email: str, password: str) -> str:
        await client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": password},
        )
        login_resp = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
        )
        return login_resp.json()["tokens"]["access_token"]

    async def test_list_empty_accounts(self, client: AsyncClient, test_password: str):
        email = "emptylist@test.com"
        token = await self._register_and_login(client, email, test_password)
        response = await client.get(
            "/api/v1/accounts",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["accounts"] == []
        assert data["total"] == 0

    async def test_list_accounts_after_create(self, client: AsyncClient, test_password: str):
        email = "listaccounts@test.com"
        token = await self._register_and_login(client, email, test_password)
        for name, acc_type in [("Banco Popular", "bank"), ("Efectivo", "cash")]:
            await client.post(
                "/api/v1/accounts",
                headers={"Authorization": f"Bearer {token}"},
                json={"name": name, "account_type": acc_type},
            )
        response = await client.get(
            "/api/v1/accounts",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2

    async def test_list_filter_by_type(self, client: AsyncClient, test_password: str):
        email = "filterlist@test.com"
        token = await self._register_and_login(client, email, test_password)
        await client.post(
            "/api/v1/accounts",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Bank", "account_type": "bank"},
        )
        await client.post(
            "/api/v1/accounts",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Cash", "account_type": "cash"},
        )
        response = await client.get(
            "/api/v1/accounts",
            headers={"Authorization": f"Bearer {token}"},
            params={"account_type": "bank"},
        )
        data = response.json()
        assert data["total"] == 1
        assert data["accounts"][0]["account_type"] == "bank"


@pytest.mark.api
class TestAccountCRUD:
    """Tests for GET/PATCH/DELETE /accounts/{id}."""

    async def _register_and_login(self, client: AsyncClient, email: str, password: str) -> str:
        await client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": password},
        )
        login_resp = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
        )
        return login_resp.json()["tokens"]["access_token"]

    async def _create_account(self, client: AsyncClient, token: str) -> str:
        resp = await client.post(
            "/api/v1/accounts",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Test Account", "account_type": "bank", "currency_code": "DOP"},
        )
        return resp.json()["id"]

    async def test_get_account(self, client: AsyncClient, test_password: str):
        email = "getacc@test.com"
        token = await self._register_and_login(client, email, test_password)
        acc_id = await self._create_account(client, token)
        response = await client.get(
            f"/api/v1/accounts/{acc_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Test Account"

    async def test_update_account(self, client: AsyncClient, test_password: str):
        email = "updateacc@test.com"
        token = await self._register_and_login(client, email, test_password)
        acc_id = await self._create_account(client, token)
        response = await client.patch(
            f"/api/v1/accounts/{acc_id}",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Updated Name", "institution": "BanReservas"},
        )
        assert response.status_code == 200
        get_resp = await client.get(
            f"/api/v1/accounts/{acc_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert get_resp.json()["name"] == "Updated Name"
        assert get_resp.json()["institution"] == "BanReservas"

    async def test_delete_account(self, client: AsyncClient, test_password: str):
        email = "deleteacc@test.com"
        token = await self._register_and_login(client, email, test_password)
        acc_id = await self._create_account(client, token)
        response = await client.delete(
            f"/api/v1/accounts/{acc_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        list_resp = await client.get(
            "/api/v1/accounts",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert list_resp.json()["total"] == 0

    async def test_get_nonexistent_account(self, client: AsyncClient, test_password: str):
        import uuid
        email = "ghostacc@test.com"
        token = await self._register_and_login(client, email, test_password)
        fake_id = uuid.uuid4()
        response = await client.get(
            f"/api/v1/accounts/{fake_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404

    async def test_account_isolation_between_users(
        self, client: AsyncClient, test_password: str
    ):
        """User A cannot see User B's accounts."""
        email_a = "usera@test.com"
        token_a = await self._register_and_login(client, email_a, test_password)
        acc_id = await self._create_account(client, token_a)

        email_b = "userb@test.com"
        token_b = await self._register_and_login(client, email_b, test_password)

        response = await client.get(
            f"/api/v1/accounts/{acc_id}",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert response.status_code == 404


@pytest.mark.api
class TestAccountSummary:
    """Tests for GET /accounts/summary."""

    async def _register_and_login(self, client: AsyncClient, email: str, password: str) -> str:
        await client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": password},
        )
        login_resp = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
        )
        return login_resp.json()["tokens"]["access_token"]

    async def test_summary_empty(self, client: AsyncClient, test_password: str):
        email = "summempty@test.com"
        token = await self._register_and_login(client, email, test_password)
        response = await client.get(
            "/api/v1/accounts/summary",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_accounts"] == 0

    async def test_summary_with_accounts(self, client: AsyncClient, test_password: str):
        email = "summdetail@test.com"
        token = await self._register_and_login(client, email, test_password)
        for name in ["Bank 1", "Bank 2"]:
            await client.post(
                "/api/v1/accounts",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "name": name,
                    "account_type": "bank",
                    "currency_code": "DOP",
                    "initial_balance": 10000,
                },
            )
        await client.post(
            "/api/v1/accounts",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "USD Account",
                "account_type": "bank",
                "currency_code": "USD",
                "initial_balance": 500,
            },
        )
        response = await client.get(
            "/api/v1/accounts/summary",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_accounts"] == 3
        assert "DOP" in data["by_currency"]
        assert "USD" in data["by_currency"]
        assert data["by_currency"]["DOP"]["account_count"] == 2
        assert data["by_currency"]["USD"]["account_count"] == 1
