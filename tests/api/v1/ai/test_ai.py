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
