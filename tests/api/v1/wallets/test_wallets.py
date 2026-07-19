"""Tests for wallet endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.api
class TestCreateWallet:
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

    async def test_create_wallet(self, client: AsyncClient, test_password: str):
        email = "walletcreate@test.com"
        token = await self._register_and_login(client, email, test_password)
        response = await client.post(
            "/api/v1/wallets",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "Mi Billetera",
                "wallet_type": "daily",
                "description": "Gastos del dia a dia",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Mi Billetera"
        assert data["wallet_type"] == "daily"
        assert data["status"] == "active"

    async def test_create_wallet_missing_name(self, client: AsyncClient, test_password: str):
        email = "walletnoname@test.com"
        token = await self._register_and_login(client, email, test_password)
        response = await client.post(
            "/api/v1/wallets",
            headers={"Authorization": f"Bearer {token}"},
            json={"wallet_type": "personal"},
        )
        assert response.status_code == 422


@pytest.mark.api
class TestWalletCRUD:
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

    async def _create_wallet(self, client: AsyncClient, token: str) -> str:
        resp = await client.post(
            "/api/v1/wallets",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Test Wallet", "wallet_type": "personal"},
        )
        return resp.json()["id"]

    async def test_get_wallet(self, client: AsyncClient, test_password: str):
        email = "getwallet@test.com"
        token = await self._register_and_login(client, email, test_password)
        wallet_id = await self._create_wallet(client, token)
        response = await client.get(
            f"/api/v1/wallets/{wallet_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Test Wallet"

    async def test_update_wallet(self, client: AsyncClient, test_password: str):
        email = "updatewallet@test.com"
        token = await self._register_and_login(client, email, test_password)
        wallet_id = await self._create_wallet(client, token)
        response = await client.patch(
            f"/api/v1/wallets/{wallet_id}",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Updated Wallet", "description": "Nueva desc"},
        )
        assert response.status_code == 200
        get_resp = await client.get(
            f"/api/v1/wallets/{wallet_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert get_resp.json()["name"] == "Updated Wallet"
        assert get_resp.json()["description"] == "Nueva desc"

    async def test_delete_wallet(self, client: AsyncClient, test_password: str):
        email = "deletewallet@test.com"
        token = await self._register_and_login(client, email, test_password)
        wallet_id = await self._create_wallet(client, token)
        response = await client.delete(
            f"/api/v1/wallets/{wallet_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        list_resp = await client.get(
            "/api/v1/wallets",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert list_resp.json()["total"] == 0

    async def test_list_wallets(self, client: AsyncClient, test_password: str):
        email = "listwallets@test.com"
        token = await self._register_and_login(client, email, test_password)
        for name in ["Wallet A", "Wallet B"]:
            await client.post(
                "/api/v1/wallets",
                headers={"Authorization": f"Bearer {token}"},
                json={"name": name, "wallet_type": "personal"},
            )
        response = await client.get(
            "/api/v1/wallets",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.json()["total"] == 2


@pytest.mark.api
class TestWalletAccounts:
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

    async def _create_wallet_and_account(self, client: AsyncClient, token: str):
        w_resp = await client.post(
            "/api/v1/wallets",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Test Wallet", "wallet_type": "daily"},
        )
        wallet_id = w_resp.json()["id"]

        a_resp = await client.post(
            "/api/v1/accounts",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Test Account", "account_type": "checking", "initial_balance": 1000},
        )
        account_id = a_resp.json()["id"]
        return wallet_id, account_id

    async def test_add_account_to_wallet(self, client: AsyncClient, test_password: str):
        email = "addacc@test.com"
        token = await self._register_and_login(client, email, test_password)
        wallet_id, account_id = await self._create_wallet_and_account(client, token)

        response = await client.post(
            f"/api/v1/wallets/{wallet_id}/accounts",
            headers={"Authorization": f"Bearer {token}"},
            json={"account_id": account_id},
        )
        assert response.status_code == 201

        detail = await client.get(
            f"/api/v1/wallets/{wallet_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert len(detail.json()["accounts"]) == 1

    async def test_remove_account_from_wallet(self, client: AsyncClient, test_password: str):
        email = "removeacc@test.com"
        token = await self._register_and_login(client, email, test_password)
        wallet_id, account_id = await self._create_wallet_and_account(client, token)

        await client.post(
            f"/api/v1/wallets/{wallet_id}/accounts",
            headers={"Authorization": f"Bearer {token}"},
            json={"account_id": account_id},
        )

        response = await client.delete(
            f"/api/v1/wallets/{wallet_id}/accounts/{account_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

        detail = await client.get(
            f"/api/v1/wallets/{wallet_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert len(detail.json()["accounts"]) == 0

    async def test_wallet_balance(self, client: AsyncClient, test_password: str):
        email = "wallbal@test.com"
        token = await self._register_and_login(client, email, test_password)
        wallet_id, account_id = await self._create_wallet_and_account(client, token)

        await client.post(
            f"/api/v1/wallets/{wallet_id}/accounts",
            headers={"Authorization": f"Bearer {token}"},
            json={"account_id": account_id},
        )

        response = await client.get(
            f"/api/v1/wallets/{wallet_id}/balance",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_accounts"] == 1

    async def test_wallet_liquidity(self, client: AsyncClient, test_password: str):
        email = "wallliq@test.com"
        token = await self._register_and_login(client, email, test_password)
        wallet_id, account_id = await self._create_wallet_and_account(client, token)

        await client.post(
            f"/api/v1/wallets/{wallet_id}/accounts",
            headers={"Authorization": f"Bearer {token}"},
            json={"account_id": account_id},
        )

        response = await client.get(
            f"/api/v1/wallets/{wallet_id}/liquidity",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["overall_level"] in ["high", "medium", "low", "mixed"]

    async def test_wallet_isolation(self, client: AsyncClient, test_password: str):
        """User A cannot see User B's wallets."""
        email_a = "wallisola@test.com"
        token_a = await self._register_and_login(client, email_a, test_password)
        w_resp = await client.post(
            "/api/v1/wallets",
            headers={"Authorization": f"Bearer {token_a}"},
            json={"name": "Secret Wallet", "wallet_type": "personal"},
        )
        wallet_id = w_resp.json()["id"]

        email_b = "wallisolb@test.com"
        token_b = await self._register_and_login(client, email_b, test_password)

        response = await client.get(
            f"/api/v1/wallets/{wallet_id}",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert response.status_code == 404
