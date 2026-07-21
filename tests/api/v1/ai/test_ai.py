"""AI API integration tests."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.api
class TestAIClassify:
    async def _register_and_login(self, client: AsyncClient, email: str, password: str) -> str:
        await client.post("/api/v1/auth/register", json={"email": email, "password": password})
        login_resp = await client.post(
            "/api/v1/auth/login", json={"email": email, "password": password}
        )
        return login_resp.json()["tokens"]["access_token"]

    async def test_classifier_status(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "ai_cls1@test.com", test_password)
        resp = await client.get(
            "/api/v1/ai/classifier/status", headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "is_trained" in data
        assert "model_version" in data

    async def test_classify_not_trained(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "ai_cls2@test.com", test_password)
        resp = await client.post(
            "/api/v1/ai/classify?transaction_id=00000000-0000-0000-0000-000000000001&description=Supermercado",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["model_version"] == "none"


@pytest.mark.api
class TestAIPredict:
    async def _register_and_login(self, client: AsyncClient, email: str, password: str) -> str:
        await client.post("/api/v1/auth/register", json={"email": email, "password": password})
        login_resp = await client.post(
            "/api/v1/auth/login", json={"email": email, "password": password}
        )
        return login_resp.json()["tokens"]["access_token"]

    async def test_predict_expenses_not_trained(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "ai_pred1@test.com", test_password)
        resp = await client.post(
            "/api/v1/ai/predict/expenses", headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "predicted_amount" in data

    async def test_predict_income_not_trained(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "ai_pred2@test.com", test_password)
        resp = await client.post(
            "/api/v1/ai/predict/income", headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "predicted_amount" in data


@pytest.mark.api
class TestAIAnomalies:
    async def _register_and_login(self, client: AsyncClient, email: str, password: str) -> str:
        await client.post("/api/v1/auth/register", json={"email": email, "password": password})
        login_resp = await client.post(
            "/api/v1/auth/login", json={"email": email, "password": password}
        )
        return login_resp.json()["tokens"]["access_token"]

    async def test_detect_anomalies_not_trained(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "ai_anom1@test.com", test_password)
        resp = await client.post(
            "/api/v1/ai/anomalies/detect", headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "anomalies" in data

    async def test_anomaly_history(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "ai_anom2@test.com", test_password)
        resp = await client.get(
            "/api/v1/ai/anomalies/history", headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "anomalies" in data
        assert "total" in data


@pytest.mark.api
class TestAIRecommendations:
    async def _register_and_login(self, client: AsyncClient, email: str, password: str) -> str:
        await client.post("/api/v1/auth/register", json={"email": email, "password": password})
        login_resp = await client.post(
            "/api/v1/auth/login", json={"email": email, "password": password}
        )
        return login_resp.json()["tokens"]["access_token"]

    async def test_get_recommendations(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "ai_rec1@test.com", test_password)
        resp = await client.post(
            "/api/v1/ai/recommendations", headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "recommendations" in data


@pytest.mark.api
class TestAIModels:
    async def _register_and_login(self, client: AsyncClient, email: str, password: str) -> str:
        await client.post("/api/v1/auth/register", json={"email": email, "password": password})
        login_resp = await client.post(
            "/api/v1/auth/login", json={"email": email, "password": password}
        )
        return login_resp.json()["tokens"]["access_token"]

    async def test_list_models(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "ai_models1@test.com", test_password)
        resp = await client.get("/api/v1/ai/models", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert "models" in data


@pytest.mark.api
class TestPhase16Habits:
    async def _register_and_login(self, client: AsyncClient, email: str, password: str) -> str:
        await client.post("/api/v1/auth/register", json={"email": email, "password": password})
        login_resp = await client.post(
            "/api/v1/auth/login", json={"email": email, "password": password}
        )
        return login_resp.json()["tokens"]["access_token"]

    async def test_habits_analysis(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "ai_hab1@test.com", test_password)
        resp = await client.get(
            "/api/v1/ai/habits/analysis", headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "habits" in data
        assert "overall_habit_score" in data

    async def test_habits_trends(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "ai_hab2@test.com", test_password)
        resp = await client.get(
            "/api/v1/ai/habits/trends", headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "trends" in data
        assert "months_analyzed" in data


@pytest.mark.api
class TestPhase16Risks:
    async def _register_and_login(self, client: AsyncClient, email: str, password: str) -> str:
        await client.post("/api/v1/auth/register", json={"email": email, "password": password})
        login_resp = await client.post(
            "/api/v1/auth/login", json={"email": email, "password": password}
        )
        return login_resp.json()["tokens"]["access_token"]

    async def test_risks_assessment(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "ai_risk1@test.com", test_password)
        resp = await client.get(
            "/api/v1/ai/risks/assessment", headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "financial_health_score" in data
        assert "risk_factors" in data
        assert "metrics" in data
        assert "recommendations" in data

    async def test_health_score(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "ai_risk2@test.com", test_password)
        resp = await client.get(
            "/api/v1/ai/risks/health-score", headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "financial_health_score" in data
        assert 0 <= data["financial_health_score"] <= 100


@pytest.mark.api
class TestPhase16Savings:
    async def _register_and_login(self, client: AsyncClient, email: str, password: str) -> str:
        await client.post("/api/v1/auth/register", json={"email": email, "password": password})
        login_resp = await client.post(
            "/api/v1/auth/login", json={"email": email, "password": password}
        )
        return login_resp.json()["tokens"]["access_token"]

    async def test_savings_optimize(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "ai_sav1@test.com", test_password)
        resp = await client.post(
            "/api/v1/ai/savings/optimize", headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "allocation_50_30_20" in data
        assert "goal_allocation" in data
        assert "debt_strategy" in data
        assert "recommendations" in data

    async def test_savings_simulate(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "ai_sav2@test.com", test_password)
        resp = await client.post(
            "/api/v1/ai/savings/simulate?monthly_amount=5000&months=12&annual_return_pct=8",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["monthly_amount"] == 5000
        assert data["months"] == 12
        assert data["final_balance"] > 5000 * 12


@pytest.mark.api
class TestPhase16Explanation:
    async def _register_and_login(self, client: AsyncClient, email: str, password: str) -> str:
        await client.post("/api/v1/auth/register", json={"email": email, "password": password})
        login_resp = await client.post(
            "/api/v1/auth/login", json={"email": email, "password": password}
        )
        return login_resp.json()["tokens"]["access_token"]

    async def test_explain_recommendation(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "ai_exp1@test.com", test_password)
        resp = await client.post(
            "/api/v1/ai/explain?rec_type=reduce_spending&title=Test&priority=high&estimated_savings=5000&confidence=0.8",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "headline" in data
        assert "why" in data
        assert "how" in data
        assert "impact" in data
        assert "action" in data
        assert "tone" in data


@pytest.mark.api
class TestPhase16Dashboard:
    async def _register_and_login(self, client: AsyncClient, email: str, password: str) -> str:
        await client.post("/api/v1/auth/register", json={"email": email, "password": password})
        login_resp = await client.post(
            "/api/v1/auth/login", json={"email": email, "password": password}
        )
        return login_resp.json()["tokens"]["access_token"]

    async def test_dashboard(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "ai_dash1@test.com", test_password)
        resp = await client.get(
            "/api/v1/ai/dashboard", headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "habits" in data
        assert "risks" in data
        assert "savings" in data
        assert "recommendations" in data
