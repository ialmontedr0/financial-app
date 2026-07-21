"""Loan API integration tests."""

from __future__ import annotations

import pytest
from httpx import AsyncClient  # noqa: TC002


@pytest.mark.api
class TestLoanCRUD:
    async def _register_and_login(self, client: AsyncClient, email: str, password: str) -> str:
        await client.post("/api/v1/auth/register", json={"email": email, "password": password})
        login_resp = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
        return login_resp.json()["tokens"]["access_token"]

    async def test_create_loan(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "loan_create1@test.com", test_password)
        resp = await client.post(
            "/api/v1/loans",
            json={
                "name": "Préstamo Personal",
                "principal_amount": 100000,
                "annual_interest_rate": 12,
                "term_months": 24,
                "loan_type": "personal",
                "lender_name": "Banco Popular",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Préstamo Personal"
        assert data["principal_amount"] == 100000
        assert data["status"] == "active"
        assert data["monthly_payment"] > 0
        assert data["amortization_entries_count"] == 24

    async def test_list_loans(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "loan_list1@test.com", test_password)
        await client.post(
            "/api/v1/loans",
            json={
                "name": "List Test",
                "principal_amount": 50000,
                "annual_interest_rate": 15,
                "term_months": 12,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        resp = await client.get(
            "/api/v1/loans",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        assert len(data["loans"]) >= 1

    async def test_get_loan_detail(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "loan_detail1@test.com", test_password)
        create = await client.post(
            "/api/v1/loans",
            json={
                "name": "Detail Test",
                "principal_amount": 75000,
                "annual_interest_rate": 10,
                "term_months": 12,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        loan_id = create.json()["id"]
        resp = await client.get(
            f"/api/v1/loans/{loan_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Detail Test"
        assert "payments_summary" in data
        assert "progress_pct" in data

    async def test_update_loan(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "loan_update1@test.com", test_password)
        create = await client.post(
            "/api/v1/loans",
            json={
                "name": "Update Test",
                "principal_amount": 50000,
                "annual_interest_rate": 12,
                "term_months": 12,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        loan_id = create.json()["id"]
        resp = await client.patch(
            f"/api/v1/loans/{loan_id}",
            json={"name": "Updated Name", "lender_name": "BanReservas"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Updated Name"
        assert resp.json()["lender_name"] == "BanReservas"

    async def test_delete_loan(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "loan_delete1@test.com", test_password)
        create = await client.post(
            "/api/v1/loans",
            json={
                "name": "Delete Test",
                "principal_amount": 30000,
                "annual_interest_rate": 20,
                "term_months": 6,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        loan_id = create.json()["id"]
        resp = await client.delete(
            f"/api/v1/loans/{loan_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["message"] == "Loan deleted successfully"

    async def test_loans_summary(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "loan_summary1@test.com", test_password)
        await client.post(
            "/api/v1/loans",
            json={
                "name": "Summary Loan",
                "principal_amount": 200000,
                "annual_interest_rate": 15,
                "term_months": 36,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        resp = await client.get(
            "/api/v1/loans/summary",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "total_balance" in data
        assert "total_monthly_payment" in data


@pytest.mark.api
class TestLoanPayments:
    async def _register_and_login(self, client: AsyncClient, email: str, password: str) -> str:
        await client.post("/api/v1/auth/register", json={"email": email, "password": password})
        login_resp = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
        return login_resp.json()["tokens"]["access_token"]

    async def _create_loan(self, client: AsyncClient, token: str) -> str:
        resp = await client.post(
            "/api/v1/loans",
            json={
                "name": "Payment Test",
                "principal_amount": 60000,
                "annual_interest_rate": 18,
                "term_months": 12,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        return resp.json()["id"]

    async def test_make_payment(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "loan_pay1@test.com", test_password)
        loan_id = await self._create_loan(client, token)
        resp = await client.post(
            f"/api/v1/loans/{loan_id}/payments",
            json={
                "amount": 6000,
                "payment_method": "bank_transfer",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["principal_portion"] > 0
        assert data["interest_portion"] > 0
        assert data["loan_status"] == "active"

    async def test_list_payments(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "loan_listpay1@test.com", test_password)
        loan_id = await self._create_loan(client, token)
        await client.post(
            f"/api/v1/loans/{loan_id}/payments",
            json={"amount": 5000},
            headers={"Authorization": f"Bearer {token}"},
        )
        resp = await client.get(
            f"/api/v1/loans/{loan_id}/payments",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        assert "summary" in data


@pytest.mark.api
class TestLoanAmortization:
    async def _register_and_login(self, client: AsyncClient, email: str, password: str) -> str:
        await client.post("/api/v1/auth/register", json={"email": email, "password": password})
        login_resp = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
        return login_resp.json()["tokens"]["access_token"]

    async def test_get_schedule(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "loan_amort1@test.com", test_password)
        create = await client.post(
            "/api/v1/loans",
            json={
                "name": "Amort Test",
                "principal_amount": 100000,
                "annual_interest_rate": 12,
                "term_months": 12,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        loan_id = create.json()["id"]
        resp = await client.get(
            f"/api/v1/loans/{loan_id}/amortization",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_entries"] == 12
        assert len(data["entries"]) == 12

    async def test_amortization_summary(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "loan_amortsum1@test.com", test_password)
        create = await client.post(
            "/api/v1/loans",
            json={
                "name": "Amort Summary",
                "principal_amount": 50000,
                "annual_interest_rate": 15,
                "term_months": 12,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        loan_id = create.json()["id"]
        resp = await client.get(
            f"/api/v1/loans/{loan_id}/amortization/summary",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_entries"] == 12
        assert data["entries_paid"] == 0
        assert data["monthly_payment"] > 0


@pytest.mark.api
class TestLoanSimulator:
    async def _register_and_login(self, client: AsyncClient, email: str, password: str) -> str:
        await client.post("/api/v1/auth/register", json={"email": email, "password": password})
        login_resp = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
        return login_resp.json()["tokens"]["access_token"]

    async def test_simulate(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "loan_sim1@test.com", test_password)
        resp = await client.post(
            "/api/v1/loans/simulate",
            json={
                "principal_amount": 200000,
                "annual_interest_rate": 15,
                "term_months": 36,
                "extra_monthly_payment": 2000,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["monthly_payment"] > 0
        assert data["total_interest"] > 0
        assert data["schedule_preview"] is not None
        assert len(data["schedule_preview"]) <= 12


@pytest.mark.api
class TestLoanEarlyPayoff:
    async def _register_and_login(self, client: AsyncClient, email: str, password: str) -> str:
        await client.post("/api/v1/auth/register", json={"email": email, "password": password})
        login_resp = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
        return login_resp.json()["tokens"]["access_token"]

    async def test_early_payoff(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "loan_payoff1@test.com", test_password)
        create = await client.post(
            "/api/v1/loans",
            json={
                "name": "Payoff Test",
                "principal_amount": 100000,
                "annual_interest_rate": 12,
                "term_months": 24,
                "early_payoff_allowed": True,
                "early_payoff_penalty_pct": 2,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        loan_id = create.json()["id"]
        resp = await client.get(
            f"/api/v1/loans/{loan_id}/early-payoff",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_payoff_amount"] > 0
        assert "interest_saved" in data
        assert data["early_payoff_penalty"] > 0
