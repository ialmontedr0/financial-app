"""Analytics API integration tests."""

from __future__ import annotations

import pytest
from httpx import AsyncClient  # noqa: TC002


@pytest.mark.api
class TestAnalyticsKPIs:
    async def _register_and_login(self, client: AsyncClient, email: str, password: str) -> str:
        await client.post("/api/v1/auth/register", json={"email": email, "password": password})
        login_resp = await client.post(
            "/api/v1/auth/login", json={"email": email, "password": password}
        )
        return login_resp.json()["tokens"]["access_token"]

    async def test_monthly_kpis(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "analytics_kpi1@test.com", test_password)
        resp = await client.get(
            "/api/v1/analytics/kpis/monthly",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "total_income" in data
        assert "total_expenses" in data
        assert "savings_rate" in data
        assert "comparison" in data

    async def test_portfolio_kpis(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "analytics_kpi2@test.com", test_password)
        resp = await client.get(
            "/api/v1/analytics/kpis/portfolio",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "net_worth" in data
        assert "debt_to_income" in data
        assert "active_budgets" in data


@pytest.mark.api
class TestAnalyticsTrends:
    async def _register_and_login(self, client: AsyncClient, email: str, password: str) -> str:
        await client.post("/api/v1/auth/register", json={"email": email, "password": password})
        login_resp = await client.post(
            "/api/v1/auth/login", json={"email": email, "password": password}
        )
        return login_resp.json()["tokens"]["access_token"]

    async def test_spending_trend(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "analytics_trend1@test.com", test_password)
        resp = await client.get(
            "/api/v1/analytics/trends/spending",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "data" in data
        assert "summary" in data

    async def test_income_trend(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "analytics_trend2@test.com", test_password)
        resp = await client.get(
            "/api/v1/analytics/trends/income",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "data" in data
        assert "summary" in data


@pytest.mark.api
class TestAnalyticsCategories:
    async def _register_and_login(self, client: AsyncClient, email: str, password: str) -> str:
        await client.post("/api/v1/auth/register", json={"email": email, "password": password})
        login_resp = await client.post(
            "/api/v1/auth/login", json={"email": email, "password": password}
        )
        return login_resp.json()["tokens"]["access_token"]

    async def test_category_breakdown(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "analytics_cat1@test.com", test_password)
        resp = await client.get(
            "/api/v1/analytics/categories/breakdown",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "categories" in data
        assert "grand_total" in data

    async def test_top_categories(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "analytics_cat2@test.com", test_password)
        resp = await client.get(
            "/api/v1/analytics/categories/top?limit=3",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "top_categories" in data
        assert len(data["top_categories"]) <= 3


@pytest.mark.api
class TestAnalyticsCashFlow:
    async def _register_and_login(self, client: AsyncClient, email: str, password: str) -> str:
        await client.post("/api/v1/auth/register", json={"email": email, "password": password})
        login_resp = await client.post(
            "/api/v1/auth/login", json={"email": email, "password": password}
        )
        return login_resp.json()["tokens"]["access_token"]

    async def test_cash_flow(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "analytics_cf1@test.com", test_password)
        resp = await client.get(
            "/api/v1/analytics/cash-flow",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "data" in data
        assert "summary" in data

    async def test_cash_flow_by_account(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "analytics_cf2@test.com", test_password)
        resp = await client.get(
            "/api/v1/analytics/cash-flow/by-account",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "accounts" in data


@pytest.mark.api
class TestAnalyticsNetWorth:
    async def _register_and_login(self, client: AsyncClient, email: str, password: str) -> str:
        await client.post("/api/v1/auth/register", json={"email": email, "password": password})
        login_resp = await client.post(
            "/api/v1/auth/login", json={"email": email, "password": password}
        )
        return login_resp.json()["tokens"]["access_token"]

    async def test_net_worth(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "analytics_nw1@test.com", test_password)
        resp = await client.get(
            "/api/v1/analytics/net-worth",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "net_worth" in data
        assert "total_assets" in data
        assert "total_liabilities" in data
        assert data["base_currency"] == "DOP"

    async def test_net_worth_converts_foreign_currency(
        self, client: AsyncClient, test_password: str, db_session
    ):
        """DOP + USD accounts: net worth sums both in the base currency (DOP)."""
        from decimal import Decimal
        from datetime import date as _date

        from app.infrastructure.currency.exchange_rate_provider import ExchangeRateProvider

        token = await self._register_and_login(client, "analytics_nw2@test.com", test_password)

        today = _date.today()
        provider = ExchangeRateProvider(db_session)
        await provider.store_rate("USD", "DOP", Decimal("100"), today)
        await db_session.commit()

        # DOP account = 1000 DOP
        r1 = await client.post(
            "/api/v1/accounts",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Pesos", "account_type": "bank", "currency_code": "DOP", "initial_balance": 1000},
        )
        assert r1.status_code == 201
        # USD account = 50 USD -> 5000 DOP at rate 100
        r2 = await client.post(
            "/api/v1/accounts",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Dolares", "account_type": "bank", "currency_code": "USD", "initial_balance": 50},
        )
        assert r2.status_code == 201

        resp = await client.get(
            "/api/v1/analytics/net-worth",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["base_currency"] == "DOP"
        # 1000 DOP + 50 USD*100 = 6000 DOP
        self.assert_close(data["total_assets"], 6000.0)
        self.assert_close(data["net_worth"], 6000.0)

    @staticmethod
    def assert_close(actual, expected, tol: float = 2.0):
        assert abs(actual - expected) <= tol, f"{actual} != {expected}"


@pytest.mark.api
class TestAnalyticsHeatmap:
    async def _register_and_login(self, client: AsyncClient, email: str, password: str) -> str:
        await client.post("/api/v1/auth/register", json={"email": email, "password": password})
        login_resp = await client.post(
            "/api/v1/auth/login", json={"email": email, "password": password}
        )
        return login_resp.json()["tokens"]["access_token"]

    async def test_spending_heatmap(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "analytics_heat1@test.com", test_password)
        resp = await client.get(
            "/api/v1/analytics/heatmaps/spending",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "data" in data
        assert "max_value" in data


@pytest.mark.api
class TestAnalyticsDashboard:
    async def _register_and_login(self, client: AsyncClient, email: str, password: str) -> str:
        await client.post("/api/v1/auth/register", json={"email": email, "password": password})
        login_resp = await client.post(
            "/api/v1/auth/login", json={"email": email, "password": password}
        )
        return login_resp.json()["tokens"]["access_token"]

    async def test_dashboard(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "analytics_dash1@test.com", test_password)
        resp = await client.get(
            "/api/v1/analytics/dashboard",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "kpis" in data
        assert "net_worth" in data
        assert "cash_flow" in data
        assert "top_categories" in data
        assert "spending_trend" in data
        assert "goals" in data
