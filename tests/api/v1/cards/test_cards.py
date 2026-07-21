"""API tests for credit card endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.api
class TestCardCRUD:
    """Test card create, read, update, delete."""

    async def _register_and_login(self, client: AsyncClient, email: str, password: str) -> str:
        await client.post("/api/v1/auth/register", json={"email": email, "password": password})
        login_resp = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
        return login_resp.json()["tokens"]["access_token"]

    async def _create_account(self, client: AsyncClient, token: str) -> str:
        resp = await client.post(
            "/api/v1/accounts",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Card Test Account", "account_type": "checking", "initial_balance": 0},
        )
        return resp.json()["id"]

    async def test_create_card(self, client: AsyncClient, test_password: str):
        email = "card_crud_create1@test.com"
        token = await self._register_and_login(client, email, test_password)
        account_id = await self._create_account(client, token)

        resp = await client.post(
            "/api/v1/cards",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "Visa Platinum",
                "account_id": account_id,
                "last_four_digits": "4532",
                "card_network": "visa",
                "credit_limit": "150000",
                "available_credit": "120000",
                "statement_day": 15,
                "payment_due_day": 5,
                "interest_rate": "0.0240",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Visa Platinum"
        assert data["card_network"] == "visa"

    async def test_list_cards(self, client: AsyncClient, test_password: str):
        email = "card_crud_list1@test.com"
        token = await self._register_and_login(client, email, test_password)
        account_id = await self._create_account(client, token)

        await client.post(
            "/api/v1/cards",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "List Card", "account_id": account_id, "credit_limit": "100000"},
        )

        resp = await client.get("/api/v1/cards", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert "cards" in data
        assert data["total"] >= 1

    async def test_get_card_detail(self, client: AsyncClient, test_password: str):
        email = "card_crud_detail1@test.com"
        token = await self._register_and_login(client, email, test_password)
        account_id = await self._create_account(client, token)

        create_resp = await client.post(
            "/api/v1/cards",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Detail Card", "account_id": account_id, "credit_limit": "200000"},
        )
        card_id = create_resp.json()["id"]

        resp = await client.get(f"/api/v1/cards/{card_id}", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Detail Card"
        assert "utilization" in data

    async def test_update_card(self, client: AsyncClient, test_password: str):
        email = "card_crud_update1@test.com"
        token = await self._register_and_login(client, email, test_password)
        account_id = await self._create_account(client, token)

        create_resp = await client.post(
            "/api/v1/cards",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Update Card", "account_id": account_id, "credit_limit": "100000"},
        )
        card_id = create_resp.json()["id"]

        resp = await client.patch(
            f"/api/v1/cards/{card_id}",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Updated Card", "credit_limit": "200000"},
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Updated Card"

    async def test_delete_card(self, client: AsyncClient, test_password: str):
        email = "card_crud_delete1@test.com"
        token = await self._register_and_login(client, email, test_password)
        account_id = await self._create_account(client, token)

        create_resp = await client.post(
            "/api/v1/cards",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Delete Card", "account_id": account_id},
        )
        card_id = create_resp.json()["id"]

        resp = await client.delete(f"/api/v1/cards/{card_id}", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200

        get_resp = await client.get(f"/api/v1/cards/{card_id}", headers={"Authorization": f"Bearer {token}"})
        assert get_resp.status_code == 404

    async def test_get_cards_summary(self, client: AsyncClient, test_password: str):
        email = "card_crud_summary1@test.com"
        token = await self._register_and_login(client, email, test_password)
        account_id = await self._create_account(client, token)

        await client.post(
            "/api/v1/cards",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Summary Card", "account_id": account_id, "credit_limit": "150000"},
        )

        resp = await client.get("/api/v1/cards/summary", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert "total_cards" in data
        assert "total_credit_limit" in data


@pytest.mark.api
class TestCardBills:
    """Test bill CRUD and payment."""

    async def _register_and_login(self, client: AsyncClient, email: str, password: str) -> str:
        await client.post("/api/v1/auth/register", json={"email": email, "password": password})
        login_resp = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
        return login_resp.json()["tokens"]["access_token"]

    async def _create_card(self, client: AsyncClient, token: str) -> str:
        account_resp = await client.post(
            "/api/v1/accounts",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Bill Account", "account_type": "checking", "initial_balance": 0},
        )
        card_resp = await client.post(
            "/api/v1/cards",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Bill Card", "account_id": account_resp.json()["id"], "credit_limit": "100000"},
        )
        return card_resp.json()["id"]

    async def test_create_bill(self, client: AsyncClient, test_password: str):
        email = "card_bill_create1@test.com"
        token = await self._register_and_login(client, email, test_password)
        card_id = await self._create_card(client, token)

        resp = await client.post(
            f"/api/v1/cards/{card_id}/bills",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "statement_date": "2026-07-01",
                "due_date": "2026-07-25",
                "total_amount": "35000",
                "minimum_payment": "1750",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["payment_status"] == "pending"

    async def test_list_bills(self, client: AsyncClient, test_password: str):
        email = "card_bill_list1@test.com"
        token = await self._register_and_login(client, email, test_password)
        card_id = await self._create_card(client, token)

        await client.post(
            f"/api/v1/cards/{card_id}/bills",
            headers={"Authorization": f"Bearer {token}"},
            json={"statement_date": "2026-07-01", "due_date": "2026-07-25", "total_amount": "20000"},
        )

        resp = await client.get(f"/api/v1/cards/{card_id}/bills", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1

    async def test_pay_bill(self, client: AsyncClient, test_password: str):
        email = "card_bill_pay1@test.com"
        token = await self._register_and_login(client, email, test_password)
        card_id = await self._create_card(client, token)

        bill_resp = await client.post(
            f"/api/v1/cards/{card_id}/bills",
            headers={"Authorization": f"Bearer {token}"},
            json={"statement_date": "2026-07-01", "due_date": "2026-07-25", "total_amount": "30000", "minimum_payment": "1500"},
        )
        bill_id = bill_resp.json()["id"]

        resp = await client.post(
            f"/api/v1/cards/{card_id}/bills/{bill_id}/pay",
            headers={"Authorization": f"Bearer {token}"},
            json={"amount": 30000, "payment_method": "manual"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["payment_status"] == "paid"


@pytest.mark.api
class TestCardLimits:
    """Test spending limits."""

    async def _register_and_login(self, client: AsyncClient, email: str, password: str) -> str:
        await client.post("/api/v1/auth/register", json={"email": email, "password": password})
        login_resp = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
        return login_resp.json()["tokens"]["access_token"]

    async def _create_card(self, client: AsyncClient, token: str) -> str:
        account_resp = await client.post(
            "/api/v1/accounts",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Limit Account", "account_type": "checking", "initial_balance": 0},
        )
        card_resp = await client.post(
            "/api/v1/cards",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Limit Card", "account_id": account_resp.json()["id"], "credit_limit": "200000"},
        )
        return card_resp.json()["id"]

    async def test_create_spending_limit(self, client: AsyncClient, test_password: str):
        email = "card_limit_create1@test.com"
        token = await self._register_and_login(client, email, test_password)
        card_id = await self._create_card(client, token)

        resp = await client.post(
            f"/api/v1/cards/{card_id}/limits",
            headers={"Authorization": f"Bearer {token}"},
            json={"limit_type": "monthly", "limit_amount": "50000", "alert_threshold": 80},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["limit_type"] == "monthly"

    async def test_list_spending_limits(self, client: AsyncClient, test_password: str):
        email = "card_limit_list1@test.com"
        token = await self._register_and_login(client, email, test_password)
        card_id = await self._create_card(client, token)

        await client.post(
            f"/api/v1/cards/{card_id}/limits",
            headers={"Authorization": f"Bearer {token}"},
            json={"limit_type": "daily", "limit_amount": "5000"},
        )

        resp = await client.get(f"/api/v1/cards/{card_id}/limits", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1

    async def test_delete_spending_limit(self, client: AsyncClient, test_password: str):
        email = "card_limit_delete1@test.com"
        token = await self._register_and_login(client, email, test_password)
        card_id = await self._create_card(client, token)

        create_resp = await client.post(
            f"/api/v1/cards/{card_id}/limits",
            headers={"Authorization": f"Bearer {token}"},
            json={"limit_type": "weekly", "limit_amount": "20000"},
        )
        limit_id = create_resp.json()["id"]

        resp = await client.delete(
            f"/api/v1/cards/{card_id}/limits/{limit_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200


@pytest.mark.api
class TestCardAlerts:
    """Test card alert endpoints."""

    async def _register_and_login(self, client: AsyncClient, email: str, password: str) -> str:
        await client.post("/api/v1/auth/register", json={"email": email, "password": password})
        login_resp = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
        return login_resp.json()["tokens"]["access_token"]

    async def test_list_alerts(self, client: AsyncClient, test_password: str):
        email = "card_alert_list1@test.com"
        token = await self._register_and_login(client, email, test_password)

        resp = await client.get("/api/v1/cards/alerts/all", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert "alerts" in data

    async def test_mark_alerts_read(self, client: AsyncClient, test_password: str):
        email = "card_alert_read1@test.com"
        token = await self._register_and_login(client, email, test_password)

        resp = await client.post(
            "/api/v1/cards/alerts/read",
            headers={"Authorization": f"Bearer {token}"},
            json={"mark_all": True},
        )
        assert resp.status_code == 200

    async def test_check_alerts(self, client: AsyncClient, test_password: str):
        email = "card_alert_check1@test.com"
        token = await self._register_and_login(client, email, test_password)

        resp = await client.post("/api/v1/cards/alerts/check", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert "new_alerts" in data
        assert "unread_alerts" in data
