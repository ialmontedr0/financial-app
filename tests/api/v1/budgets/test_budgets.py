"""API tests for budget endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.api
class TestBudgetCRUD:
    """Test budget create, read, update, delete."""

    async def _register_and_login(self, client: AsyncClient, email: str, password: str) -> str:
        await client.post("/api/v1/auth/register", json={"email": email, "password": password})
        login_resp = await client.post(
            "/api/v1/auth/login", json={"email": email, "password": password}
        )
        return login_resp.json()["tokens"]["access_token"]

    async def _create_account(self, client: AsyncClient, token: str) -> str:
        resp = await client.post(
            "/api/v1/accounts",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Budget Test Account", "account_type": "checking", "initial_balance": 0},
        )
        return resp.json()["id"]

    async def test_create_total_budget(self, client: AsyncClient, test_password: str):
        email = "budget_create1@test.com"
        token = await self._register_and_login(client, email, test_password)

        resp = await client.post(
            "/api/v1/budgets",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "Presupuesto Mensual",
                "amount": "50000",
                "budget_type": "total",
                "period": "monthly",
                "alert_threshold": 80,
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Presupuesto Mensual"
        assert data["budget_type"] == "total"
        assert float(data["amount"]) == 50000.0

    async def test_list_budgets(self, client: AsyncClient, test_password: str):
        email = "budget_list1@test.com"
        token = await self._register_and_login(client, email, test_password)

        await client.post(
            "/api/v1/budgets",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "List Budget", "amount": "30000", "budget_type": "total"},
        )

        resp = await client.get("/api/v1/budgets", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert "budgets" in data
        assert "total" in data
        assert data["total"] >= 1

    async def test_get_budget_summary(self, client: AsyncClient, test_password: str):
        email = "budget_summary1@test.com"
        token = await self._register_and_login(client, email, test_password)

        await client.post(
            "/api/v1/budgets",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Summary Budget", "amount": "40000", "budget_type": "total"},
        )

        resp = await client.get(
            "/api/v1/budgets/summary", headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "total_budgets" in data
        assert "total_spent" in data

    async def test_get_budget_detail(self, client: AsyncClient, test_password: str):
        email = "budget_detail1@test.com"
        token = await self._register_and_login(client, email, test_password)

        create_resp = await client.post(
            "/api/v1/budgets",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Detail Budget", "amount": "25000", "budget_type": "total"},
        )
        budget_id = create_resp.json()["id"]

        resp = await client.get(
            f"/api/v1/budgets/{budget_id}", headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Detail Budget"
        assert "pct_used" in data
        assert "status" in data

    async def test_update_budget(self, client: AsyncClient, test_password: str):
        email = "budget_update1@test.com"
        token = await self._register_and_login(client, email, test_password)

        create_resp = await client.post(
            "/api/v1/budgets",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Update Budget", "amount": "30000", "budget_type": "total"},
        )
        budget_id = create_resp.json()["id"]

        resp = await client.patch(
            f"/api/v1/budgets/{budget_id}",
            headers={"Authorization": f"Bearer {token}"},
            json={"amount": "35000", "alert_threshold": 75},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert float(data["amount"]) == 35000.0
        assert data["alert_threshold"] == 75

    async def test_refresh_budget(self, client: AsyncClient, test_password: str):
        email = "budget_refresh1@test.com"
        token = await self._register_and_login(client, email, test_password)

        create_resp = await client.post(
            "/api/v1/budgets",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Refresh Budget", "amount": "50000", "budget_type": "total"},
        )
        budget_id = create_resp.json()["id"]

        resp = await client.post(
            f"/api/v1/budgets/{budget_id}/refresh",
            headers={"Authorization": f"Bearer {token}"},
            json={},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "spent" in data
        assert "remaining" in data
        assert "status" in data

    async def test_delete_budget(self, client: AsyncClient, test_password: str):
        email = "budget_delete1@test.com"
        token = await self._register_and_login(client, email, test_password)

        create_resp = await client.post(
            "/api/v1/budgets",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Delete Budget", "amount": "20000", "budget_type": "total"},
        )
        budget_id = create_resp.json()["id"]

        resp = await client.delete(
            f"/api/v1/budgets/{budget_id}", headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 200

        get_resp = await client.get(
            f"/api/v1/budgets/{budget_id}", headers={"Authorization": f"Bearer {token}"}
        )
        assert get_resp.status_code == 404


@pytest.mark.api
class TestBudgetAlerts:
    """Test budget alert endpoints."""

    async def _register_and_login(self, client: AsyncClient, email: str, password: str) -> str:
        await client.post("/api/v1/auth/register", json={"email": email, "password": password})
        login_resp = await client.post(
            "/api/v1/auth/login", json={"email": email, "password": password}
        )
        return login_resp.json()["tokens"]["access_token"]

    async def test_list_alerts(self, client: AsyncClient, test_password: str):
        email = "budget_alerts1@test.com"
        token = await self._register_and_login(client, email, test_password)

        resp = await client.get(
            "/api/v1/budgets/alerts/all", headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "alerts" in data

    async def test_mark_alert_read(self, client: AsyncClient, test_password: str):
        email = "budget_alerts2@test.com"
        token = await self._register_and_login(client, email, test_password)

        resp = await client.post(
            "/api/v1/budgets/alerts/read",
            headers={"Authorization": f"Bearer {token}"},
            json={"mark_all": True},
        )
        assert resp.status_code == 200

    async def test_auto_adjust_budget(self, client: AsyncClient, test_password: str):
        email = "budget_adjust1@test.com"
        token = await self._register_and_login(client, email, test_password)

        create_resp = await client.post(
            "/api/v1/budgets",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "Adjust Budget",
                "amount": "50000",
                "budget_type": "total",
                "auto_adjust": True,
            },
        )
        budget_id = create_resp.json()["id"]

        resp = await client.post(
            f"/api/v1/budgets/{budget_id}/auto-adjust",
            headers={"Authorization": f"Bearer {token}"},
            json={"buffer_pct": 10, "apply": False},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "current_amount" in data
        assert "suggested_amount" in data
