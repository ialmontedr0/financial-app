"""API tests for lent loans (préstamo otorgado)."""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy import update

from app.infrastructure.models.lent_loan import LentLoanModel


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

    async def test_simulate_single_payment(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "lent_sim3@test.com", test_password)
        resp = await client.post(
            "/api/v1/lent-loans/simulate",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "principal_amount": 10000,
                "annual_interest_rate": 12,
                "payment_frequency": "single_payment",
                "single_payment_date": "2026-12",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["payment_frequency"] == "single_payment"
        assert data["single_payment_date"] == "2026-12-31"
        assert data["term_months"] > 0
        assert data["monthly_payment"] > data["principal_amount"]
        assert data["total_to_receive"] > data["principal_amount"]
        assert len(data["schedule_preview"]) == 1

    async def test_simulate_single_payment_zero_interest(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "lent_sim4@test.com", test_password)
        resp = await client.post(
            "/api/v1/lent-loans/simulate",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "principal_amount": 5000,
                "annual_interest_rate": 0,
                "payment_frequency": "single_payment",
                "single_payment_date": "2026-12",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["monthly_payment"] == 5000
        assert data["total_interest"] == 0

    async def test_simulate_single_payment_requires_date(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "lent_sim5@test.com", test_password)
        resp = await client.post(
            "/api/v1/lent-loans/simulate",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "principal_amount": 10000,
                "annual_interest_rate": 12,
                "payment_frequency": "single_payment",
            },
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

    async def test_create_single_payment(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "lent_single@test.com", test_password)
        resp = await client.post(
            "/api/v1/lent-loans",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "borrower_name": "María Rodríguez",
                "principal_amount": 12000,
                "annual_interest_rate": 18,
                "payment_frequency": "single_payment",
                "single_payment_date": "2026-12",
                "currency_code": "DOP",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["payment_frequency"] == "single_payment"
        assert data["single_payment_date"] == "2026-12-31"
        assert data["monthly_payment"] > data["principal_amount"]
        assert data["current_balance"] == 12000
        assert len(data["schedule"]) == 1
        assert data["schedule"][0]["due_date"] == "2026-12-31"
        assert data["schedule"][0]["amount"] == data["monthly_payment"]
        assert data["schedule"][0]["balance_after"] == 0

        detail = await client.get(
            f"/api/v1/lent-loans/{data['id']}", headers={"Authorization": f"Bearer {token}"}
        )
        assert detail.status_code == 200
        assert detail.json()["single_payment_date"] == "2026-12-31"

    async def test_create_single_payment_requires_date(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "lent_single2@test.com", test_password)
        resp = await client.post(
            "/api/v1/lent-loans",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "borrower_name": "Carlos García",
                "principal_amount": 12000,
                "annual_interest_rate": 18,
                "payment_frequency": "single_payment",
                "currency_code": "DOP",
            },
        )
        assert resp.status_code == 422


@pytest.mark.api
class TestLentLoanAccountIntegration:
    """El préstamo se descuenta de la cuenta origen y los cobros se acreditan."""

    async def _register_and_login(self, client: AsyncClient, email: str, password: str) -> str:
        await client.post("/api/v1/auth/register", json={"email": email, "password": password})
        login = await client.post(
            "/api/v1/auth/login", json={"email": email, "password": password}
        )
        return login.json()["tokens"]["access_token"]

    async def _create_account(self, client: AsyncClient, token: str, balance: float) -> str:
        resp = await client.post(
            "/api/v1/accounts",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "Cuenta Origen",
                "account_type": "bank",
                "currency_code": "DOP",
                "initial_balance": balance,
                "institution": "Test Bank",
                "account_number_last4": "7777",
            },
        )
        assert resp.status_code == 201
        return resp.json()["id"]

    async def _account_balance(self, client: AsyncClient, token: str, account_id: str) -> float:
        resp = await client.get(
            f"/api/v1/accounts/{account_id}", headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 200
        return float(resp.json()["balance"])

    async def _create_loan(
        self, client: AsyncClient, token: str, account_id: str, principal: float = 5000
    ) -> dict:
        resp = await client.post(
            "/api/v1/lent-loans",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "borrower_name": "Ana Torres",
                "principal_amount": principal,
                "annual_interest_rate": 24,
                "term_months": 6,
                "currency_code": "DOP",
                "account_id": account_id,
            },
        )
        assert resp.status_code == 201
        return resp.json()

    async def test_create_loan_deducts_from_account(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "lent_acct1@test.com", test_password)
        account_id = await self._create_account(client, token, 50000.0)

        await self._create_loan(client, token, account_id)

        assert await self._account_balance(client, token, account_id) == 45000.0

    async def test_record_payment_credits_account(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "lent_acct2@test.com", test_password)
        account_id = await self._create_account(client, token, 50000.0)
        loan = await self._create_loan(client, token, account_id)

        resp = await client.post(
            f"/api/v1/lent-loans/{loan['id']}/payments",
            headers={"Authorization": f"Bearer {token}"},
            json={"amount": loan["monthly_payment"], "payment_method": "cash"},
        )
        assert resp.status_code == 201

        assert await self._account_balance(client, token, account_id) == pytest.approx(
            45000.0 + loan["monthly_payment"]
        )

    async def test_delete_loan_returns_outstanding_balance(
        self, client: AsyncClient, test_password: str
    ):
        token = await self._register_and_login(client, "lent_acct3@test.com", test_password)
        account_id = await self._create_account(client, token, 50000.0)
        loan = await self._create_loan(client, token, account_id)

        resp = await client.delete(
            f"/api/v1/lent-loans/{loan['id']}", headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 200

        assert await self._account_balance(client, token, account_id) == 50000.0

    async def test_delete_after_partial_payment_keeps_interest(
        self, client: AsyncClient, test_password: str
    ):
        token = await self._register_and_login(client, "lent_acct4@test.com", test_password)
        account_id = await self._create_account(client, token, 50000.0)
        loan = await self._create_loan(client, token, account_id)

        pay_resp = await client.post(
            f"/api/v1/lent-loans/{loan['id']}/payments",
            headers={"Authorization": f"Bearer {token}"},
            json={"amount": loan["monthly_payment"], "payment_method": "cash"},
        )
        assert pay_resp.status_code == 201
        interest_received = pay_resp.json()["total_interest_received"]

        del_resp = await client.delete(
            f"/api/v1/lent-loans/{loan['id']}", headers={"Authorization": f"Bearer {token}"}
        )
        assert del_resp.status_code == 200

        # El capital se recupera íntegro (cobros + saldo devuelto); el interés
        # cobrado queda como ganancia en la cuenta.
        assert await self._account_balance(client, token, account_id) == pytest.approx(
            50000.0 + interest_received
        )

    async def test_create_loan_with_foreign_account_fails(
        self, client: AsyncClient, test_password: str
    ):
        token = await self._register_and_login(client, "lent_acct5@test.com", test_password)
        account_id = await self._create_account(client, token, 50000.0)

        other = await self._register_and_login(client, "lent_acct6@test.com", test_password)
        resp = await client.post(
            "/api/v1/lent-loans",
            headers={"Authorization": f"Bearer {other}"},
            json={
                "borrower_name": "Impostor",
                "principal_amount": 1000,
                "annual_interest_rate": 12,
                "term_months": 3,
                "currency_code": "DOP",
                "account_id": account_id,
            },
        )
        assert resp.status_code == 422
        assert resp.json()["detail"] == "La cuenta de origen no existe"


@pytest.mark.api
class TestLentLoanReceivables:
    """Endpoint de cuentas por cobrar (préstamos otorgados pendientes)."""

    async def _register_and_login(self, client: AsyncClient, email: str, password: str) -> str:
        await client.post("/api/v1/auth/register", json={"email": email, "password": password})
        login = await client.post(
            "/api/v1/auth/login", json={"email": email, "password": password}
        )
        return login.json()["tokens"]["access_token"]

    async def _create_loan(self, client: AsyncClient, token: str, borrower: str) -> dict:
        resp = await client.post(
            "/api/v1/lent-loans",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "borrower_name": borrower,
                "principal_amount": 5000,
                "annual_interest_rate": 24,
                "term_months": 6,
                "currency_code": "DOP",
            },
        )
        assert resp.status_code == 201
        return resp.json()

    async def test_lists_active_and_defaulted(
        self, client: AsyncClient, db_session, test_password: str
    ):
        token = await self._register_and_login(client, "lent_recv1@test.com", test_password)
        loan1 = await self._create_loan(client, token, "Deudor Uno")
        await self._create_loan(client, token, "Deudor Dos")

        await db_session.execute(
            update(LentLoanModel).where(LentLoanModel.id == loan1["id"]).values(status="defaulted")
        )
        await db_session.commit()

        resp = await client.get(
            "/api/v1/lent-loans/receivables", headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        assert data["summary"]["count"] == 2
        assert data["summary"]["count_overdue"] == 1
        assert data["summary"]["total_overdue"] == 5000
        assert data["summary"]["total_outstanding"] == 10000
        assert data["summary"]["total_principal"] == 10000
        assert data["items"][0]["status"] == "defaulted"

    async def test_excludes_paid_off(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "lent_recv2@test.com", test_password)
        resp = await client.post(
            "/api/v1/lent-loans",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "borrower_name": "Pago Unico",
                "principal_amount": 5000,
                "annual_interest_rate": 18,
                "payment_frequency": "single_payment",
                "single_payment_date": "2026-12",
                "currency_code": "DOP",
            },
        )
        assert resp.status_code == 201
        loan = resp.json()

        pay = await client.post(
            f"/api/v1/lent-loans/{loan['id']}/payments",
            headers={"Authorization": f"Bearer {token}"},
            json={"amount": loan["current_balance"], "payment_method": "bank_transfer"},
        )
        assert pay.status_code == 201
        assert pay.json()["status"] == "paid_off"

        recv = await client.get(
            "/api/v1/lent-loans/receivables", headers={"Authorization": f"Bearer {token}"}
        )
        assert recv.status_code == 200
        assert recv.json()["total"] == 0
        assert recv.json()["summary"]["total_outstanding"] == 0
