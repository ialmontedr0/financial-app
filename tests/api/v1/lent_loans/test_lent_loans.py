"""API tests for lent loans (préstamo otorgado)."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.api
class TestLentLoanSimulate:
    async def _register_and_login(self, client: AsyncClient, email: str, password: str) -> str:
        await client.post("/api/v1/auth/register", json={"email": email, "password": password})
        login = await client.post(
            "/api/v1/auth/login", json={"email": email, "password": password}
        )
        return login.json()["tokens"]["access_token"]

    async def test_simulate_loan(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "lent_sim@test.com", test_password)
        resp = await client.post(
            "/api/v1/lent-loans/simulate",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "principal_amount": 10000,
                "annual_interest_rate": 12,
                "term_months": 12,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["monthly_payment"] > 0
        assert data["total_interest"] > 0
        assert data["principal_amount"] == 10000
        assert "schedule_preview" in data

    async def test_simulate_validation(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "lent_sim2@test.com", test_password)
        resp = await client.post(
            "/api/v1/lent-loans/simulate",
            headers={"Authorization": f"Bearer {token}"},
            json={"principal_amount": -5, "annual_interest_rate": 12, "term_months": 12},
        )
        assert resp.status_code == 422


@pytest.mark.api
class TestLentLoanCRUD:
    async def _register_and_login(self, client: AsyncClient, email: str, password: str) -> str:
        await client.post("/api/v1/auth/register", json={"email": email, "password": password})
        login = await client.post(
            "/api/v1/auth/login", json={"email": email, "password": password}
        )
        return login.json()["tokens"]["access_token"]

    async def _create_loan(self, client: AsyncClient, token: str) -> dict:
        resp = await client.post(
            "/api/v1/lent-loans",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "borrower_name": "Juan Pérez",
                "principal_amount": 5000,
                "annual_interest_rate": 24,
                "term_months": 6,
                "currency_code": "DOP",
            },
        )
        assert resp.status_code == 201
        return resp.json()

    async def test_create_list_get(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "lent_crud@test.com", test_password)
        created = await self._create_loan(client, token)
        assert created["borrower_name"] == "Juan Pérez"
        assert created["status"] == "active"
        assert created["current_balance"] == 5000
        assert isinstance(created["monthly_payment"], float)
        assert "schedule" in created

        loan_id = created["id"]

        listed = await client.get(
            "/api/v1/lent-loans", headers={"Authorization": f"Bearer {token}"}
        )
        assert listed.status_code == 200
        assert listed.json()["total"] == 1

        detail = await client.get(
            f"/api/v1/lent-loans/{loan_id}", headers={"Authorization": f"Bearer {token}"}
        )
        assert detail.status_code == 200
        assert detail.json()["id"] == loan_id
        assert "schedule" in detail.json()
        assert "payments" in detail.json()

    async def test_record_payment_pays_balance(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "lent_pay@test.com", test_password)
        created = await self._create_loan(client, token)
        loan_id = created["id"]

        payment_amt = created["monthly_payment"]
        resp = await client.post(
            f"/api/v1/lent-loans/{loan_id}/payments",
            headers={"Authorization": f"Bearer {token}"},
            json={"amount": payment_amt, "payment_method": "cash"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["total_received"] == payment_amt
        assert data["current_balance"] < data["principal_amount"]

    async def test_summary(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "lent_sum@test.com", test_password)
        await self._create_loan(client, token)
        resp = await client.get(
            "/api/v1/lent-loans/summary", headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["asset_class"] == "lent_loan"
        assert data["count"] == 1
        assert data["total_outstanding"] == 5000

    async def test_delete(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "lent_del@test.com", test_password)
        created = await self._create_loan(client, token)
        resp = await client.delete(
            f"/api/v1/lent-loans/{created['id']}", headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 200
        listed = await client.get(
            "/api/v1/lent-loans", headers={"Authorization": f"Bearer {token}"}
        )
        assert listed.json()["total"] == 0