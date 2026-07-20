"""API tests for financial goal endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.api
class TestGoalCRUD:
    async def _register_and_login(self, client: AsyncClient, email: str, password: str) -> str:
        await client.post("/api/v1/auth/register", json={"email": email, "password": password})
        login_resp = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
        return login_resp.json()["tokens"]["access_token"]

    async def test_create_goal(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "goal_create1@test.com", test_password)
        resp = await client.post("/api/v1/goals", headers={"Authorization": f"Bearer {token}"},
            json={"name": "Emergency Fund", "target_amount": "500000", "goal_type": "emergency_fund", "monthly_contribution": "25000"})
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Emergency Fund"
        assert float(data["target_amount"]) == 500000.0
        assert "prediction" in data

    async def test_list_goals(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "goal_list1@test.com", test_password)
        await client.post("/api/v1/goals", headers={"Authorization": f"Bearer {token}"},
            json={"name": "Goal 1", "target_amount": "100000"})
        resp = await client.get("/api/v1/goals", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

    async def test_get_goal_summary(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "goal_summary1@test.com", test_password)
        resp = await client.get("/api/v1/goals/summary", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert "total_goals" in resp.json()

    async def test_get_goal_detail(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "goal_detail1@test.com", test_password)
        create_resp = await client.post("/api/v1/goals", headers={"Authorization": f"Bearer {token}"},
            json={"name": "Detail Goal", "target_amount": "200000"})
        goal_id = create_resp.json()["id"]
        resp = await client.get(f"/api/v1/goals/{goal_id}", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert "progress" in resp.json()
        assert "milestones" in resp.json()

    async def test_update_goal(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "goal_update1@test.com", test_password)
        create_resp = await client.post("/api/v1/goals", headers={"Authorization": f"Bearer {token}"},
            json={"name": "Update Goal", "target_amount": "150000"})
        goal_id = create_resp.json()["id"]
        resp = await client.patch(f"/api/v1/goals/{goal_id}", headers={"Authorization": f"Bearer {token}"},
            json={"target_amount": "200000", "priority": 2})
        assert resp.status_code == 200
        assert float(resp.json()["target_amount"]) == 200000.0

    async def test_delete_goal(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "goal_delete1@test.com", test_password)
        create_resp = await client.post("/api/v1/goals", headers={"Authorization": f"Bearer {token}"},
            json={"name": "Delete Goal", "target_amount": "50000"})
        goal_id = create_resp.json()["id"]
        resp = await client.delete(f"/api/v1/goals/{goal_id}", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200

    async def test_refresh_goal(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "goal_refresh1@test.com", test_password)
        create_resp = await client.post("/api/v1/goals", headers={"Authorization": f"Bearer {token}"},
            json={"name": "Refresh Goal", "target_amount": "300000"})
        goal_id = create_resp.json()["id"]
        resp = await client.post(f"/api/v1/goals/{goal_id}/refresh", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert "progress" in resp.json()
        assert "prediction" in resp.json()


@pytest.mark.api
class TestGoalSimulations:
    async def _register_and_login(self, client: AsyncClient, email: str, password: str) -> str:
        await client.post("/api/v1/auth/register", json={"email": email, "password": password})
        login_resp = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
        return login_resp.json()["tokens"]["access_token"]

    async def test_create_simulation(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "goal_sim1@test.com", test_password)
        create_resp = await client.post("/api/v1/goals", headers={"Authorization": f"Bearer {token}"},
            json={"name": "Sim Goal", "target_amount": "500000"})
        goal_id = create_resp.json()["id"]
        resp = await client.post(f"/api/v1/goals/{goal_id}/simulations", headers={"Authorization": f"Bearer {token}"},
            json={"name": "Conservative", "monthly_contribution": "20000", "interest_rate": "6"})
        assert resp.status_code == 201
        assert "projection" in resp.json()

    async def test_list_simulations(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "goal_sim2@test.com", test_password)
        create_resp = await client.post("/api/v1/goals", headers={"Authorization": f"Bearer {token}"},
            json={"name": "List Sim Goal", "target_amount": "300000"})
        goal_id = create_resp.json()["id"]
        resp = await client.get(f"/api/v1/goals/{goal_id}/simulations", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200

    async def test_refresh_prediction(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "goal_pred1@test.com", test_password)
        create_resp = await client.post("/api/v1/goals", headers={"Authorization": f"Bearer {token}"},
            json={"name": "Predict Goal", "target_amount": "200000"})
        goal_id = create_resp.json()["id"]
        resp = await client.post(f"/api/v1/goals/{goal_id}/predict", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert "prediction" in resp.json()
