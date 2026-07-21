"""Phase 17 Automation API tests."""

import pytest
from httpx import AsyncClient


@pytest.mark.api
class TestAutomationCRUD:
    async def _register_and_login(
        self, client: AsyncClient, email: str, password: str
    ) -> str:
        await client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": password},
        )
        login_resp = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
        )
        return login_resp.json()["tokens"]["access_token"]

    async def test_list_rules_empty(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "auto_list1@test.com", test_password)
        resp = await client.get(
            "/api/v1/automations",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "rules" in data
        assert data["total"] == 0

    async def test_create_rule(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "auto_create1@test.com", test_password)
        resp = await client.post(
            "/api/v1/automations",
            json={
                "name": "Ahorro automatico",
                "trigger_type": "date_scheduled",
                "action_type": "create_transaction",
                "trigger_conditions": {
                    "day_of_month": 1,
                    "months": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
                },
                "action_params": {
                    "account_id": "00000000-0000-0000-0000-000000000001",
                    "amount": 5000,
                    "description": "Ahorro mensual",
                    "transaction_type": "expense",
                },
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert "id" in data
        assert data["name"] == "Ahorro automatico"

    async def test_create_rule_invalid_trigger(
        self, client: AsyncClient, test_password: str
    ):
        token = await self._register_and_login(client, "auto_create2@test.com", test_password)
        resp = await client.post(
            "/api/v1/automations",
            json={
                "name": "Bad rule",
                "trigger_type": "invalid_trigger",
                "action_type": "transfer",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert "error" in data

    async def test_get_templates(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "auto_tmpl1@test.com", test_password)
        resp = await client.get(
            "/api/v1/automations/templates",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "triggers" in data
        assert "actions" in data
        assert len(data["triggers"]) >= 5
        assert len(data["actions"]) >= 4


@pytest.mark.api
class TestAutomationExecution:
    async def _register_and_login(
        self, client: AsyncClient, email: str, password: str
    ) -> str:
        await client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": password},
        )
        login_resp = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
        )
        return login_resp.json()["tokens"]["access_token"]

    async def test_evaluate_all(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "auto_eval1@test.com", test_password)
        resp = await client.post(
            "/api/v1/automations/evaluate?dry_run=true",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "total_rules" in data
        assert "executed" in data

    async def test_summary(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "auto_sum1@test.com", test_password)
        resp = await client.get(
            "/api/v1/automations/summary",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "total_rules" in data
        assert "active_rules" in data


@pytest.mark.api
class TestAutomationExecutionLog:
    async def _register_and_login(
        self, client: AsyncClient, email: str, password: str
    ) -> str:
        await client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": password},
        )
        login_resp = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
        )
        return login_resp.json()["tokens"]["access_token"]

    async def test_execution_log_empty(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "auto_log1@test.com", test_password)
        resp = await client.get(
            "/api/v1/automations/execution-log",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "logs" in data
        assert data["total"] == 0
