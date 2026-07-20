"""Tests for transaction endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.api
class TestCreateTransaction:
    async def _register_and_login(self, client: AsyncClient, email: str, password: str) -> str:
        await client.post("/api/v1/auth/register", json={"email": email, "password": password})
        login_resp = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
        return login_resp.json()["tokens"]["access_token"]

    async def _create_account(self, client: AsyncClient, token: str) -> str:
        resp = await client.post("/api/v1/accounts", headers={"Authorization": f"Bearer {token}"},
            json={"name": "Test Account", "account_type": "checking", "initial_balance": 50000})
        return resp.json()["id"]

    async def test_create_expense(self, client: AsyncClient, test_password: str):
        email = "txcreate1@test.com"
        token = await self._register_and_login(client, email, test_password)
        acc_id = await self._create_account(client, token)

        response = await client.post("/api/v1/transactions", headers={"Authorization": f"Bearer {token}"},
            json={"account_id": acc_id, "transaction_type": "expense", "amount": 1500.50,
                  "description": "Supermercado", "effective_date": "2026-07-19"})
        assert response.status_code == 201
        data = response.json()
        assert data["transaction_type"] == "expense"
        assert data["amount"] == "1500.5000"
        assert data["status"] == "completed"

    async def test_create_income(self, client: AsyncClient, test_password: str):
        email = "txcreate2@test.com"
        token = await self._register_and_login(client, email, test_password)
        acc_id = await self._create_account(client, token)

        response = await client.post("/api/v1/transactions", headers={"Authorization": f"Bearer {token}"},
            json={"account_id": acc_id, "transaction_type": "income", "amount": 85000,
                  "description": "Salario mensual", "effective_date": "2026-07-01"})
        assert response.status_code == 201
        assert response.json()["transaction_type"] == "income"

    async def test_create_with_tags(self, client: AsyncClient, test_password: str):
        email = "txcreate3@test.com"
        token = await self._register_and_login(client, email, test_password)
        acc_id = await self._create_account(client, token)

        response = await client.post("/api/v1/transactions", headers={"Authorization": f"Bearer {token}"},
            json={"account_id": acc_id, "transaction_type": "expense", "amount": 500,
                  "description": "Gasolina", "effective_date": "2026-07-19", "tags": ["transporte", "mensual"]})
        assert response.status_code == 201
        assert set(response.json()["tags"]) == {"transporte", "mensual"}

    async def test_create_invalid_amount(self, client: AsyncClient, test_password: str):
        email = "txcreate4@test.com"
        token = await self._register_and_login(client, email, test_password)
        acc_id = await self._create_account(client, token)

        response = await client.post("/api/v1/transactions", headers={"Authorization": f"Bearer {token}"},
            json={"account_id": acc_id, "transaction_type": "expense", "amount": -100,
                  "description": "Negative", "effective_date": "2026-07-19"})
        assert response.status_code == 422


@pytest.mark.api
class TestTransactionCRUD:
    async def _setup(self, client: AsyncClient, email: str, test_password: str):
        token_resp = await client.post("/api/v1/auth/register", json={"email": email, "password": test_password})
        login_resp = await client.post("/api/v1/auth/login", json={"email": email, "password": test_password})
        token = login_resp.json()["tokens"]["access_token"]
        acc_resp = await client.post("/api/v1/accounts", headers={"Authorization": f"Bearer {token}"},
            json={"name": "Test Acc", "account_type": "checking", "initial_balance": 50000})
        acc_id = acc_resp.json()["id"]
        return token, acc_id

    async def test_list_transactions(self, client: AsyncClient, test_password: str):
        email = "txlist1@test.com"
        token, acc_id = await self._setup(client, email, test_password)
        for i in range(3):
            await client.post("/api/v1/transactions", headers={"Authorization": f"Bearer {token}"},
                json={"account_id": acc_id, "transaction_type": "expense", "amount": 100 * (i + 1),
                      "description": f"Purchase {i}", "effective_date": "2026-07-19"})
        response = await client.get("/api/v1/transactions", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        assert response.json()["total"] == 3

    async def test_get_transaction_detail(self, client: AsyncClient, test_password: str):
        email = "txdetail@test.com"
        token, acc_id = await self._setup(client, email, test_password)
        create_resp = await client.post("/api/v1/transactions", headers={"Authorization": f"Bearer {token}"},
            json={"account_id": acc_id, "transaction_type": "expense", "amount": 2500,
                  "description": "Detailed tx", "effective_date": "2026-07-19"})
        tx_id = create_resp.json()["id"]
        response = await client.get(f"/api/v1/transactions/{tx_id}", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        assert response.json()["description"] == "Detailed tx"
        assert "tags" in response.json()
        assert "attachments" in response.json()

    async def test_delete_transaction(self, client: AsyncClient, test_password: str):
        email = "txdel1@test.com"
        token, acc_id = await self._setup(client, email, test_password)
        create_resp = await client.post("/api/v1/transactions", headers={"Authorization": f"Bearer {token}"},
            json={"account_id": acc_id, "transaction_type": "expense", "amount": 100,
                  "description": "To delete", "effective_date": "2026-07-19"})
        tx_id = create_resp.json()["id"]
        response = await client.delete(f"/api/v1/transactions/{tx_id}", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        assert response.json()["status"] == "cancelled"


@pytest.mark.api
class TestTransfer:
    async def _setup(self, client: AsyncClient, email: str, test_password: str):
        login_resp = await client.post("/api/v1/auth/register", json={"email": email, "password": test_password})
        if login_resp.status_code != 201:
            login_resp = await client.post("/api/v1/auth/login", json={"email": email, "password": test_password})
        token = login_resp.json()["tokens"]["access_token"]
        acc1 = await client.post("/api/v1/accounts", headers={"Authorization": f"Bearer {token}"},
            json={"name": "Account A", "account_type": "checking", "initial_balance": 50000})
        acc2 = await client.post("/api/v1/accounts", headers={"Authorization": f"Bearer {token}"},
            json={"name": "Account B", "account_type": "savings", "initial_balance": 10000})
        return token, acc1.json()["id"], acc2.json()["id"]

    async def test_create_transfer(self, client: AsyncClient, test_password: str):
        email = "txtransfer@test.com"
        token, acc1_id, acc2_id = await self._setup(client, email, test_password)

        response = await client.post("/api/v1/transactions/transfer", headers={"Authorization": f"Bearer {token}"},
            json={"source_account_id": acc1_id, "destination_account_id": acc2_id,
                  "amount": 5000, "description": "Transferencia test", "effective_date": "2026-07-19"})
        assert response.status_code == 201
        data = response.json()
        assert "transfer_id" in data
        assert data["source_transaction"]["type"] == "expense"
        assert data["destination_transaction"]["type"] == "income"
        assert data["total_amount"] == "5000"

    async def test_transfer_same_account_fails(self, client: AsyncClient, test_password: str):
        email = "txtransfer2@test.com"
        token, acc1_id, _ = await self._setup(client, email, test_password)

        response = await client.post("/api/v1/transactions/transfer", headers={"Authorization": f"Bearer {token}"},
            json={"source_account_id": acc1_id, "destination_account_id": acc1_id,
                  "amount": 1000, "description": "Same account", "effective_date": "2026-07-19"})
        assert response.status_code == 422


@pytest.mark.api
class TestTags:
    async def _setup(self, client: AsyncClient, email: str, test_password: str):
        login_resp = await client.post("/api/v1/auth/register", json={"email": email, "password": test_password})
        if login_resp.status_code != 201:
            login_resp = await client.post("/api/v1/auth/login", json={"email": email, "password": test_password})
        token = login_resp.json()["tokens"]["access_token"]
        acc_resp = await client.post("/api/v1/accounts", headers={"Authorization": f"Bearer {token}"},
            json={"name": "Test Acc", "account_type": "checking", "initial_balance": 50000})
        acc_id = acc_resp.json()["id"]
        tx_resp = await client.post("/api/v1/transactions", headers={"Authorization": f"Bearer {token}"},
            json={"account_id": acc_id, "transaction_type": "expense", "amount": 500,
                  "description": "Tagged tx", "effective_date": "2026-07-19"})
        return token, tx_resp.json()["id"]

    async def test_add_and_remove_tags(self, client: AsyncClient, test_password: str):
        email = "txtags1@test.com"
        token, tx_id = await self._setup(client, email, test_password)

        resp = await client.post(f"/api/v1/transactions/{tx_id}/tags", headers={"Authorization": f"Bearer {token}"},
            json={"tags": ["groceries", "weekly"]})
        assert resp.status_code == 201
        assert "groceries" in resp.json()["all_tags"]

        resp = await client.delete(f"/api/v1/transactions/{tx_id}/tags/groceries",
            headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert "groceries" not in resp.json()["remaining_tags"]


@pytest.mark.api
class TestSummary:
    async def _setup(self, client: AsyncClient, email: str, test_password: str):
        login_resp = await client.post("/api/v1/auth/register", json={"email": email, "password": test_password})
        if login_resp.status_code != 201:
            login_resp = await client.post("/api/v1/auth/login", json={"email": email, "password": test_password})
        token = login_resp.json()["tokens"]["access_token"]
        acc_resp = await client.post("/api/v1/accounts", headers={"Authorization": f"Bearer {token}"},
            json={"name": "Test Acc", "account_type": "checking", "initial_balance": 100000})
        return token, acc_resp.json()["id"]

    async def test_summary(self, client: AsyncClient, test_password: str):
        email = "txsummary@test.com"
        token, acc_id = await self._setup(client, email, test_password)

        await client.post("/api/v1/transactions", headers={"Authorization": f"Bearer {token}"},
            json={"account_id": acc_id, "transaction_type": "income", "amount": 50000,
                  "description": "Salary", "effective_date": "2026-07-15"})
        await client.post("/api/v1/transactions", headers={"Authorization": f"Bearer {token}"},
            json={"account_id": acc_id, "transaction_type": "expense", "amount": 15000,
                  "description": "Rent", "effective_date": "2026-07-01"})

        response = await client.get("/api/v1/transactions/summary?date_from=2026-07-01&date_to=2026-07-31",
            headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        data = response.json()
        assert data["total_income"] == "50000.0000"
        assert data["total_expenses"] == "15000.0000"
        assert data["net_flow"] == "35000.0000"


@pytest.mark.api
class TestRecurring:
    async def _setup(self, client: AsyncClient, email: str, test_password: str):
        login_resp = await client.post("/api/v1/auth/register", json={"email": email, "password": test_password})
        if login_resp.status_code != 201:
            login_resp = await client.post("/api/v1/auth/login", json={"email": email, "password": test_password})
        token = login_resp.json()["tokens"]["access_token"]
        acc_resp = await client.post("/api/v1/accounts", headers={"Authorization": f"Bearer {token}"},
            json={"name": "Test Acc", "account_type": "checking", "initial_balance": 50000})
        return token, acc_resp.json()["id"]

    async def test_create_and_list_recurring(self, client: AsyncClient, test_password: str):
        email = "txrecurring@test.com"
        token, acc_id = await self._setup(client, email, test_password)

        resp = await client.post("/api/v1/transactions/recurring", headers={"Authorization": f"Bearer {token}"},
            json={"account_id": acc_id, "transaction_type": "expense", "amount": 2500,
                  "description": "Alquiler mensual", "frequency": "monthly", "start_date": "2026-08-01"})
        assert resp.status_code == 201
        rec_id = resp.json()["id"]
        assert resp.json()["frequency"] == "monthly"
        assert resp.json()["is_active"] is True

        resp = await client.get("/api/v1/transactions/recurring", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1


@pytest.mark.api
class TestOCR:
    async def _register_and_login(self, client: AsyncClient, email: str, password: str) -> str:
        await client.post("/api/v1/auth/register", json={"email": email, "password": password})
        login_resp = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
        return login_resp.json()["tokens"]["access_token"]

    async def test_ocr_stub(self, client: AsyncClient, test_password: str):
        email = "txocr@test.com"
        token = await self._register_and_login(client, email, test_password)
        response = await client.post("/api/v1/transactions/ocr", headers={"Authorization": f"Bearer {token}"},
            json={"image_url": "https://example.com/receipt.jpg"})
        assert response.status_code == 200
        assert response.json()["success"] is False
        assert "Fase 20" in response.json()["message"]


@pytest.mark.api
class TestTransactionIsolation:
    async def test_user_cannot_see_other_users_transaction(self, client: AsyncClient, test_password: str):
        await client.post("/api/v1/auth/register", json={"email": "txisoA@test.com", "password": test_password})
        login_a = await client.post("/api/v1/auth/login", json={"email": "txisoA@test.com", "password": test_password})
        token_a = login_a.json()["tokens"]["access_token"]
        acc_resp = await client.post("/api/v1/accounts", headers={"Authorization": f"Bearer {token_a}"},
            json={"name": "A Account", "account_type": "checking", "initial_balance": 50000})
        acc_id = acc_resp.json()["id"]
        tx_resp = await client.post("/api/v1/transactions", headers={"Authorization": f"Bearer {token_a}"},
            json={"account_id": acc_id, "transaction_type": "expense", "amount": 1000,
                  "description": "Secret tx", "effective_date": "2026-07-19"})
        tx_id = tx_resp.json()["id"]

        await client.post("/api/v1/auth/register", json={"email": "txisoB@test.com", "password": test_password})
        login_b = await client.post("/api/v1/auth/login", json={"email": "txisoB@test.com", "password": test_password})
        token_b = login_b.json()["tokens"]["access_token"]

        response = await client.get(f"/api/v1/transactions/{tx_id}", headers={"Authorization": f"Bearer {token_b}"})
        assert response.status_code == 404
