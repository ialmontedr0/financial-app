"""API tests for financial goal endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.api
class TestGoalCRUD:
    async def _register_and_login(self, client: AsyncClient, email: str, password: str) -> str:
        await client.post("/api/v1/auth/register", json={"email": email, "password": password})
        login_resp = await client.post(
            "/api/v1/auth/login", json={"email": email, "password": password}
        )
        return login_resp.json()["tokens"]["access_token"]

    async def test_create_goal(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "goal_create1@test.com", test_password)
        resp = await client.post(
            "/api/v1/goals",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "Emergency Fund",
                "target_amount": "500000",
                "goal_type": "emergency_fund",
                "monthly_contribution": "25000",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Emergency Fund"
        assert float(data["target_amount"]) == 500000.0
        assert "prediction" in data

    async def test_list_goals(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "goal_list1@test.com", test_password)
        await client.post(
            "/api/v1/goals",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Goal 1", "target_amount": "100000"},
        )
        resp = await client.get("/api/v1/goals", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

    async def test_get_goal_summary(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "goal_summary1@test.com", test_password)
        resp = await client.get(
            "/api/v1/goals/summary", headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 200
        assert "total_goals" in resp.json()

    async def test_get_goal_detail(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "goal_detail1@test.com", test_password)
        create_resp = await client.post(
            "/api/v1/goals",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Detail Goal", "target_amount": "200000"},
        )
        goal_id = create_resp.json()["id"]
        resp = await client.get(
            f"/api/v1/goals/{goal_id}", headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 200
        assert "progress" in resp.json()
        assert "milestones" in resp.json()

    async def test_update_goal(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "goal_update1@test.com", test_password)
        create_resp = await client.post(
            "/api/v1/goals",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Update Goal", "target_amount": "150000"},
        )
        goal_id = create_resp.json()["id"]
        resp = await client.patch(
            f"/api/v1/goals/{goal_id}",
            headers={"Authorization": f"Bearer {token}"},
            json={"target_amount": "200000", "priority": 2},
        )
        assert resp.status_code == 200
        assert float(resp.json()["target_amount"]) == 200000.0

    async def test_delete_goal(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "goal_delete1@test.com", test_password)
        create_resp = await client.post(
            "/api/v1/goals",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Delete Goal", "target_amount": "50000"},
        )
        goal_id = create_resp.json()["id"]
        resp = await client.delete(
            f"/api/v1/goals/{goal_id}", headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 200

    async def test_refresh_goal(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "goal_refresh1@test.com", test_password)
        create_resp = await client.post(
            "/api/v1/goals",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Refresh Goal", "target_amount": "300000"},
        )
        goal_id = create_resp.json()["id"]
        resp = await client.post(
            f"/api/v1/goals/{goal_id}/refresh", headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 200
        assert "progress" in resp.json()
        assert "prediction" in resp.json()


@pytest.mark.api
class TestGoalSimulations:
    async def _register_and_login(self, client: AsyncClient, email: str, password: str) -> str:
        await client.post("/api/v1/auth/register", json={"email": email, "password": password})
        login_resp = await client.post(
            "/api/v1/auth/login", json={"email": email, "password": password}
        )
        return login_resp.json()["tokens"]["access_token"]

    async def test_create_simulation(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "goal_sim1@test.com", test_password)
        create_resp = await client.post(
            "/api/v1/goals",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Sim Goal", "target_amount": "500000"},
        )
        goal_id = create_resp.json()["id"]
        resp = await client.post(
            f"/api/v1/goals/{goal_id}/simulations",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Conservative", "monthly_contribution": "20000", "interest_rate": "6"},
        )
        assert resp.status_code == 201
        assert "projection" in resp.json()

    async def test_list_simulations(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "goal_sim2@test.com", test_password)
        create_resp = await client.post(
            "/api/v1/goals",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "List Sim Goal", "target_amount": "300000"},
        )
        goal_id = create_resp.json()["id"]
        resp = await client.get(
            f"/api/v1/goals/{goal_id}/simulations", headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 200

    async def test_refresh_prediction(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "goal_pred1@test.com", test_password)
        create_resp = await client.post(
            "/api/v1/goals",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Predict Goal", "target_amount": "200000"},
        )
        goal_id = create_resp.json()["id"]
        resp = await client.post(
            f"/api/v1/goals/{goal_id}/predict", headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 200
        assert "prediction" in resp.json()

    async def test_preview_simulation_does_not_persist(
        self, client: AsyncClient, test_password: str
    ):
        token = await self._register_and_login(client, "goal_simprev@test.com", test_password)
        create_resp = await client.post(
            "/api/v1/goals",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Preview Sim Goal", "target_amount": "500000"},
        )
        goal_id = create_resp.json()["id"]
        resp = await client.post(
            f"/api/v1/goals/{goal_id}/simulations",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Preview", "monthly_contribution": "20000", "preview": True},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["id"] is None
        assert data["saved"] is False
        assert "projection" in data
        assert data["starting_amount"] == "0.00"

        list_resp = await client.get(
            f"/api/v1/goals/{goal_id}/simulations", headers={"Authorization": f"Bearer {token}"}
        )
        assert list_resp.status_code == 200
        assert list_resp.json()["total"] == 0

    async def test_simulation_includes_initial_amount_in_projection(
        self, client: AsyncClient, test_password: str
    ):
        token = await self._register_and_login(client, "goal_siminit@test.com", test_password)
        await client.post(
            "/api/v1/accounts",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "Banco Sim",
                "account_type": "bank",
                "currency_code": "DOP",
                "initial_balance": 240740.0,
                "institution": "Test Bank",
                "account_number_last4": "1111",
            },
        )
        create_resp = await client.post(
            "/api/v1/goals",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "Init Amount Goal",
                "target_amount": "500000",
                "start_from_zero": False,
                "monthly_contribution": "31988",
            },
        )
        goal_id = create_resp.json()["id"]
        resp = await client.post(
            f"/api/v1/goals/{goal_id}/simulations",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "With Patrimony", "monthly_contribution": "31988", "preview": True},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["starting_amount"] == "240740.00"
        proj = data["projection"]
        assert proj and proj[0]["cumulative"] > 240740.0

    async def test_simulation_yearly_income_anchored_to_start_month(
        self, client: AsyncClient, test_password: str
    ):
        token = await self._register_and_login(client, "goal_simbonus@test.com", test_password)
        create_resp = await client.post(
            "/api/v1/goals",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Bonus Goal", "target_amount": "500000", "monthly_contribution": "31988"},
        )
        goal_id = create_resp.json()["id"]
        resp = await client.post(
            f"/api/v1/goals/{goal_id}/simulations",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "With Bonus",
                "monthly_contribution": "31988",
                "preview": True,
                "income_sources": [
                    {
                        "name": "Bono navideno",
                        "amount": 31525,
                        "frequency": "yearly",
                        "start_month": 5,
                    },
                ],
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        proj = data["projection"]
        month5 = next((p for p in proj if p["month"] == 5), None)
        assert month5 is not None
        assert month5["income_contribution"] > 30000


@pytest.mark.api
class TestGoalStartingAmount:
    """Tests for the patrimony/initial-amount behavior on goal creation."""

    async def _register_and_login(self, client: AsyncClient, email: str, password: str) -> str:
        await client.post("/api/v1/auth/register", json={"email": email, "password": password})
        login_resp = await client.post(
            "/api/v1/auth/login", json={"email": email, "password": password}
        )
        return login_resp.json()["tokens"]["access_token"]

    async def _create_account(self, client: AsyncClient, token: str, balance: float) -> None:
        resp = await client.post(
            "/api/v1/accounts",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "Banco Test",
                "account_type": "bank",
                "currency_code": "DOP",
                "initial_balance": balance,
                "institution": "Test Bank",
                "account_number_last4": "9999",
            },
        )
        assert resp.status_code == 201

    async def test_goal_without_start_from_zero_includes_assets(
        self, client: AsyncClient, test_password: str
    ):
        token = await self._register_and_login(client, "goal_assets1@test.com", test_password)
        await self._create_account(client, token, 75000.0)

        resp = await client.post(
            "/api/v1/goals",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Asset Seed Goal", "target_amount": "300000", "start_from_zero": False},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Asset Seed Goal"
        assert float(data["initial_amount"]) == 75000.0
        assert float(data["current_amount"]) == 75000.0

        goal_id = data["id"]
        detail = await client.get(
            f"/api/v1/goals/{goal_id}", headers={"Authorization": f"Bearer {token}"}
        )
        assert detail.status_code == 200
        assert float(detail.json()["progress"]["current_amount"]) == 75000.0
        assert detail.json()["progress"]["pct_complete"] == 25.0

    async def test_goal_with_start_from_zero_starts_at_zero(
        self, client: AsyncClient, test_password: str
    ):
        token = await self._register_and_login(client, "goal_assets2@test.com", test_password)
        await self._create_account(client, token, 75000.0)

        resp = await client.post(
            "/api/v1/goals",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Zero Seed Goal", "target_amount": "300000", "start_from_zero": True},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert float(data["initial_amount"]) == 0.0
        assert float(data["current_amount"]) == 0.0

    async def test_goal_default_is_start_from_zero(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "goal_assets3@test.com", test_password)
        await self._create_account(client, token, 75000.0)

        resp = await client.post(
            "/api/v1/goals",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Default Goal", "target_amount": "300000"},
        )
        assert resp.status_code == 201
        assert float(resp.json()["current_amount"]) == 0.0


@pytest.mark.api
class TestGoalTransactionIntegration:
    """El avance de la meta refleja los ingresos y gastos del usuario."""

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
            json={
                "name": "Banco Metas",
                "account_type": "bank",
                "currency_code": "DOP",
                "initial_balance": 100000.0,
                "institution": "Test Bank",
                "account_number_last4": "5555",
            },
        )
        assert resp.status_code == 201
        return resp.json()["id"]

    async def _create_transaction(
        self,
        client: AsyncClient,
        token: str,
        account_id: str,
        tx_type: str,
        amount: float,
    ) -> None:
        from datetime import UTC, datetime

        resp = await client.post(
            "/api/v1/transactions",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "account_id": account_id,
                "transaction_type": tx_type,
                "amount": amount,
                "currency_code": "DOP",
                "description": f"Tx {tx_type} {amount}",
                "effective_date": datetime.now(UTC).date().isoformat(),
            },
        )
        assert resp.status_code == 201

    async def test_goal_progress_reflects_income_and_expenses(
        self, client: AsyncClient, test_password: str
    ):
        token = await self._register_and_login(client, "goal_tx1@test.com", test_password)
        account_id = await self._create_account(client, token)

        goal_resp = await client.post(
            "/api/v1/goals",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Meta con transacciones", "target_amount": "200000"},
        )
        assert goal_resp.status_code == 201
        goal_id = goal_resp.json()["id"]

        await self._create_transaction(client, token, account_id, "income", 50000)
        detail = await client.get(
            f"/api/v1/goals/{goal_id}", headers={"Authorization": f"Bearer {token}"}
        )
        assert float(detail.json()["progress"]["current_amount"]) == 50000.0

        await self._create_transaction(client, token, account_id, "expense", 20000)
        detail = await client.get(
            f"/api/v1/goals/{goal_id}", headers={"Authorization": f"Bearer {token}"}
        )
        assert float(detail.json()["progress"]["current_amount"]) == 30000.0

    async def test_goal_progress_clamps_at_zero_with_high_expenses(
        self, client: AsyncClient, test_password: str
    ):
        token = await self._register_and_login(client, "goal_tx2@test.com", test_password)
        account_id = await self._create_account(client, token)

        goal_resp = await client.post(
            "/api/v1/goals",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Meta con gastos", "target_amount": "200000"},
        )
        assert goal_resp.status_code == 201
        goal_id = goal_resp.json()["id"]

        await self._create_transaction(client, token, account_id, "income", 10000)
        await self._create_transaction(client, token, account_id, "expense", 30000)
        detail = await client.get(
            f"/api/v1/goals/{goal_id}", headers={"Authorization": f"Bearer {token}"}
        )
        assert float(detail.json()["progress"]["current_amount"]) == 0.0
        assert float(detail.json()["progress"]["pct_complete"]) == 0.0


@pytest.mark.api
class TestGoalPatrimonyIntegration:
    """La meta que inicia desde el patrimonio sigue el saldo real de los activos."""

    async def _register_and_login(self, client: AsyncClient, email: str, password: str) -> str:
        await client.post("/api/v1/auth/register", json={"email": email, "password": password})
        login_resp = await client.post(
            "/api/v1/auth/login", json={"email": email, "password": password}
        )
        return login_resp.json()["tokens"]["access_token"]

    async def _create_account(self, client: AsyncClient, token: str, balance: float = 50000.0) -> str:
        resp = await client.post(
            "/api/v1/accounts",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "Cuenta Patrimonio",
                "account_type": "bank",
                "currency_code": "DOP",
                "initial_balance": balance,
                "institution": "Test Bank",
                "account_number_last4": "1111",
            },
        )
        assert resp.status_code == 201
        return resp.json()["id"]

    async def _create_goal(
        self, client: AsyncClient, token: str, start_from_zero: bool
    ) -> dict:
        resp = await client.post(
            "/api/v1/goals",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "Meta patrimonio",
                "target_amount": "200000",
                "start_from_zero": start_from_zero,
            },
        )
        assert resp.status_code == 201
        return resp.json()

    async def _create_lent_loan(
        self, client: AsyncClient, token: str, account_id: str
    ) -> None:
        resp = await client.post(
            "/api/v1/lent-loans",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "borrower_name": "Prestatario",
                "principal_amount": 5000,
                "annual_interest_rate": 24,
                "term_months": 6,
                "currency_code": "DOP",
                "account_id": account_id,
            },
        )
        assert resp.status_code == 201

    async def _goal_current_amount(
        self, client: AsyncClient, token: str, goal_id: str
    ) -> float:
        detail = await client.get(
            f"/api/v1/goals/{goal_id}", headers={"Authorization": f"Bearer {token}"}
        )
        assert detail.status_code == 200
        return float(detail.json()["current_amount"])

    async def test_goal_from_patrimony_keeps_value_when_lent_loan_disburses(
        self, client: AsyncClient, test_password: str
    ):
        token = await self._register_and_login(client, "goal_pat1@test.com", test_password)
        account_id = await self._create_account(client, token)

        goal = await self._create_goal(client, token, start_from_zero=False)
        assert float(goal["current_amount"]) == 50000.0

        # El desembolso baja el saldo de la cuenta, pero el prestamo queda como
        # cuenta por cobrar: el patrimonio no se reduce.
        await self._create_lent_loan(client, token, account_id)

        assert await self._goal_current_amount(client, token, goal["id"]) == 50000.0

    async def test_net_worth_keeps_value_when_lent_loan_disburses(
        self, client: AsyncClient, test_password: str
    ):
        token = await self._register_and_login(client, "goal_pat3@test.com", test_password)
        account_id = await self._create_account(client, token)

        nw = await client.get(
            "/api/v1/analytics/net-worth", headers={"Authorization": f"Bearer {token}"}
        )
        assert nw.status_code == 200
        assert nw.json()["total_assets"] == 50000.0

        await self._create_lent_loan(client, token, account_id)

        nw = await client.get(
            "/api/v1/analytics/net-worth", headers={"Authorization": f"Bearer {token}"}
        )
        assert nw.status_code == 200
        assert nw.json()["total_assets"] == 50000.0
        assert "investment" in nw.json()["assets_by_type"]

    async def test_start_from_zero_goal_ignores_account_balance_changes(
        self, client: AsyncClient, test_password: str
    ):
        token = await self._register_and_login(client, "goal_pat2@test.com", test_password)
        account_id = await self._create_account(client, token)

        goal = await self._create_goal(client, token, start_from_zero=True)
        assert float(goal["current_amount"]) == 0.0

        await self._create_lent_loan(client, token, account_id)

        assert await self._goal_current_amount(client, token, goal["id"]) == 0.0
