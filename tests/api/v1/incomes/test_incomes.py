"""API tests for income endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.api
class TestCreateIncome:
    async def _register_and_login(self, client: AsyncClient, email: str, password: str) -> str:
        await client.post("/api/v1/auth/register", json={"email": email, "password": password})
        login_resp = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
        return login_resp.json()["tokens"]["access_token"]

    async def _create_account(self, client: AsyncClient, token: str) -> str:
        resp = await client.post("/api/v1/accounts", headers={"Authorization": f"Bearer {token}"},
            json={"name": "Income Test Account", "account_type": "checking", "initial_balance": 0})
        return resp.json()["id"]

    async def test_create_income(self, client: AsyncClient, test_password: str):
        email = "income_crud1@test.com"
        token = await self._register_and_login(client, email, test_password)
        acc_id = await self._create_account(client, token)

        resp = await client.post("/api/v1/incomes", headers={"Authorization": f"Bearer {token}"},
            json={"account_id": acc_id, "amount": 85000,
                  "description": "Salario mensual", "effective_date": "2026-07-01",
                  "income_type": "salary", "stability": "fixed"})
        assert resp.status_code == 201
        data = resp.json()
        assert data["income_type"] == "salary"
        assert data["amount"] == "85000.0000"
        assert "id" in data
        assert "transaction_id" in data

    async def test_create_income_with_tags(self, client: AsyncClient, test_password: str):
        email = "income_crud2@test.com"
        token = await self._register_and_login(client, email, test_password)
        acc_id = await self._create_account(client, token)

        resp = await client.post("/api/v1/incomes", headers={"Authorization": f"Bearer {token}"},
            json={"account_id": acc_id, "amount": 15000,
                  "description": "Freelance project", "effective_date": "2026-07-15",
                  "income_type": "freelance", "tags": ["web", "client-a"]})
        assert resp.status_code == 201
        assert "web" in resp.json()["tags"]


@pytest.mark.api
class TestIncomeCRUD:
    async def _register_and_login(self, client: AsyncClient, email: str, password: str) -> str:
        await client.post("/api/v1/auth/register", json={"email": email, "password": password})
        login_resp = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
        return login_resp.json()["tokens"]["access_token"]

    async def _create_account(self, client: AsyncClient, token: str) -> str:
        resp = await client.post("/api/v1/accounts", headers={"Authorization": f"Bearer {token}"},
            json={"name": "Income CRUD Account", "account_type": "checking", "initial_balance": 0})
        return resp.json()["id"]

    async def test_list_incomes(self, client: AsyncClient, test_password: str):
        email = "income_list1@test.com"
        token = await self._register_and_login(client, email, test_password)
        acc_id = await self._create_account(client, token)

        await client.post("/api/v1/incomes", headers={"Authorization": f"Bearer {token}"},
            json={"account_id": acc_id, "amount": 50000,
                  "description": "List test income", "effective_date": "2026-07-01"})

        resp = await client.get("/api/v1/incomes", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert "incomes" in data
        assert data["total"] >= 1

    async def test_get_income_detail(self, client: AsyncClient, test_password: str):
        email = "income_detail1@test.com"
        token = await self._register_and_login(client, email, test_password)
        acc_id = await self._create_account(client, token)

        create_resp = await client.post("/api/v1/incomes", headers={"Authorization": f"Bearer {token}"},
            json={"account_id": acc_id, "amount": 5000,
                  "description": "Detail test income", "effective_date": "2026-07-20",
                  "income_type": "bonus"})
        income_id = create_resp.json()["id"]
        resp = await client.get(f"/api/v1/incomes/{income_id}", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert resp.json()["income_type"] == "bonus"

    async def test_delete_income(self, client: AsyncClient, test_password: str):
        email = "income_del1@test.com"
        token = await self._register_and_login(client, email, test_password)
        acc_id = await self._create_account(client, token)

        create_resp = await client.post("/api/v1/incomes", headers={"Authorization": f"Bearer {token}"},
            json={"account_id": acc_id, "amount": 3000,
                  "description": "To delete", "effective_date": "2026-07-20"})
        income_id = create_resp.json()["id"]
        resp = await client.delete(f"/api/v1/incomes/{income_id}", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200


@pytest.mark.api
class TestIncomeSources:
    async def _register_and_login(self, client: AsyncClient, email: str, password: str) -> str:
        await client.post("/api/v1/auth/register", json={"email": email, "password": password})
        login_resp = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
        return login_resp.json()["tokens"]["access_token"]

    async def test_create_source(self, client: AsyncClient, test_password: str):
        email = "income_src1@test.com"
        token = await self._register_and_login(client, email, test_password)

        resp = await client.post("/api/v1/incomes/sources", headers={"Authorization": f"Bearer {token}"},
            json={"name": "Tech Corp", "income_type": "salary",
                  "stability": "fixed", "frequency": "monthly"})
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Tech Corp"
        assert data["income_type"] == "salary"

    async def test_list_sources(self, client: AsyncClient, test_password: str):
        email = "income_src2@test.com"
        token = await self._register_and_login(client, email, test_password)

        await client.post("/api/v1/incomes/sources", headers={"Authorization": f"Bearer {token}"},
            json={"name": "List Corp", "income_type": "freelance"})

        resp = await client.get("/api/v1/incomes/sources", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1


@pytest.mark.api
class TestIncomeSchedule:
    async def _register_and_login(self, client: AsyncClient, email: str, password: str) -> str:
        await client.post("/api/v1/auth/register", json={"email": email, "password": password})
        login_resp = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
        return login_resp.json()["tokens"]["access_token"]

    async def _create_account(self, client: AsyncClient, token: str) -> str:
        resp = await client.post("/api/v1/accounts", headers={"Authorization": f"Bearer {token}"},
            json={"name": "Schedule Account", "account_type": "checking", "initial_balance": 0})
        return resp.json()["id"]

    async def test_create_schedule(self, client: AsyncClient, test_password: str):
        email = "income_sched1@test.com"
        token = await self._register_and_login(client, email, test_password)
        acc_id = await self._create_account(client, token)

        resp = await client.post("/api/v1/incomes/schedule", headers={"Authorization": f"Bearer {token}"},
            json={"description": "Freelance payment expected",
                  "amount": 25000, "account_id": acc_id,
                  "expected_date": "2026-08-15"})
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "projected"
        assert data["amount"] == "25000.0"

    async def test_list_schedule(self, client: AsyncClient, test_password: str):
        email = "income_sched2@test.com"
        token = await self._register_and_login(client, email, test_password)
        acc_id = await self._create_account(client, token)

        await client.post("/api/v1/incomes/schedule", headers={"Authorization": f"Bearer {token}"},
            json={"description": "Schedule list test", "amount": 10000,
                  "account_id": acc_id, "expected_date": "2026-09-01"})

        resp = await client.get("/api/v1/incomes/schedule", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1


@pytest.mark.api
class TestIncomeAnalytics:
    async def _register_and_login(self, client: AsyncClient, email: str, password: str) -> str:
        await client.post("/api/v1/auth/register", json={"email": email, "password": password})
        login_resp = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
        return login_resp.json()["tokens"]["access_token"]

    async def _create_account(self, client: AsyncClient, token: str) -> str:
        resp = await client.post("/api/v1/accounts", headers={"Authorization": f"Bearer {token}"},
            json={"name": "Analytics Account", "account_type": "checking", "initial_balance": 0})
        return resp.json()["id"]

    async def test_summary(self, client: AsyncClient, test_password: str):
        email = "income_analytics1@test.com"
        token = await self._register_and_login(client, email, test_password)
        acc_id = await self._create_account(client, token)

        await client.post("/api/v1/incomes", headers={"Authorization": f"Bearer {token}"},
            json={"account_id": acc_id, "amount": 85000,
                  "description": "Summary test salary", "effective_date": "2026-07-01",
                  "income_type": "salary"})

        resp = await client.get("/api/v1/incomes/summary?date_from=2026-01-01&date_to=2026-12-31",
            headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert "total_income" in data
        assert "by_type" in data

    async def test_trends(self, client: AsyncClient, test_password: str):
        email = "income_analytics2@test.com"
        token = await self._register_and_login(client, email, test_password)
        acc_id = await self._create_account(client, token)

        await client.post("/api/v1/incomes", headers={"Authorization": f"Bearer {token}"},
            json={"account_id": acc_id, "amount": 85000,
                  "description": "Trends test", "effective_date": "2026-07-01"})

        resp = await client.get("/api/v1/incomes/trends?months=6",
            headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert "trend" in resp.json()

    async def test_forecast(self, client: AsyncClient, test_password: str):
        email = "income_analytics3@test.com"
        token = await self._register_and_login(client, email, test_password)
        acc_id = await self._create_account(client, token)

        await client.post("/api/v1/incomes", headers={"Authorization": f"Bearer {token}"},
            json={"account_id": acc_id, "amount": 85000,
                  "description": "Forecast test", "effective_date": "2026-07-01"})

        resp = await client.get("/api/v1/incomes/forecast",
            headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert "projected_monthly" in resp.json()

    async def test_by_source(self, client: AsyncClient, test_password: str):
        email = "income_analytics4@test.com"
        token = await self._register_and_login(client, email, test_password)
        acc_id = await self._create_account(client, token)

        await client.post("/api/v1/incomes", headers={"Authorization": f"Bearer {token}"},
            json={"account_id": acc_id, "amount": 85000,
                  "description": "By source test", "effective_date": "2026-07-01"})

        resp = await client.get("/api/v1/incomes/by-source?date_from=2026-01-01&date_to=2026-12-31",
            headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert "sources" in resp.json()

    async def test_monthly_breakdown(self, client: AsyncClient, test_password: str):
        email = "income_analytics5@test.com"
        token = await self._register_and_login(client, email, test_password)
        acc_id = await self._create_account(client, token)

        await client.post("/api/v1/incomes", headers={"Authorization": f"Bearer {token}"},
            json={"account_id": acc_id, "amount": 85000,
                  "description": "Monthly breakdown test", "effective_date": "2026-07-01"})

        resp = await client.get("/api/v1/incomes/monthly/2026/7",
            headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert resp.json()["month"] == 7

    async def test_recurring_candidates(self, client: AsyncClient, test_password: str):
        email = "income_analytics6@test.com"
        token = await self._register_and_login(client, email, test_password)
        acc_id = await self._create_account(client, token)

        await client.post("/api/v1/incomes", headers={"Authorization": f"Bearer {token}"},
            json={"account_id": acc_id, "amount": 85000,
                  "description": "Recurring candidates test", "effective_date": "2026-07-01"})

        resp = await client.get("/api/v1/incomes/recurring-candidates",
            headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert "total_candidates" in resp.json()
