"""Investments API integration tests."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient


def _iso(days_from_today: int = 0) -> str:
    return (datetime.now(UTC).date() + timedelta(days=days_from_today)).isoformat()


@pytest.mark.api
class TestInvestmentsCRUD:
    async def _register_and_login(self, client: AsyncClient, email: str, password: str) -> str:
        await client.post("/api/v1/auth/register", json={"email": email, "password": password})
        login_resp = await client.post(
            "/api/v1/auth/login", json={"email": email, "password": password}
        )
        return login_resp.json()["tokens"]["access_token"]

    async def _create_asset(
        self,
        client: AsyncClient,
        token: str,
        name: str = "Apple",
        asset_type: str = "stock",
        current_price: float = 190.5,
        currency: str = "USD",
        symbol: str = "AAPL",
    ) -> dict:
        resp = await client.post(
            "/api/v1/investments/assets",
            json={
                "name": name,
                "asset_type": asset_type,
                "current_price": current_price,
                "currency": currency,
                "symbol": symbol,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201, resp.text
        return resp.json()

    async def _create_portfolio(
        self, client: AsyncClient, token: str, name: str = "Portafolio Principal"
    ) -> dict:
        resp = await client.post(
            "/api/v1/investments/portfolios",
            json={"name": name, "description": "Mis inversiones"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201, resp.text
        return resp.json()

    async def test_create_asset(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "inv_cr1@test.com", test_password)
        data = await self._create_asset(client, token)
        assert data["name"] == "Apple"
        assert data["asset_type"] == "stock"
        assert data["symbol"] == "AAPL"
        assert data["currency"] == "USD"
        assert data["current_price"] == 190.5

    async def test_create_asset_invalid_type(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "inv_cr2@test.com", test_password)
        resp = await client.post(
            "/api/v1/investments/assets",
            json={"name": "Oro", "asset_type": "forex"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422

    async def test_create_asset_invalid_currency(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "inv_cr3@test.com", test_password)
        resp = await client.post(
            "/api/v1/investments/assets",
            json={"name": "Euro", "asset_type": "crypto", "currency": "XXX"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422

    async def test_list_assets(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "inv_cr4@test.com", test_password)
        await self._create_asset(client, token, name="Bitcoin", asset_type="crypto")
        await self._create_asset(client, token, name="VOO", asset_type="etf", symbol="VOO")
        resp = await client.get(
            "/api/v1/investments/assets", headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        assert {a["name"] for a in data["assets"]} == {"Bitcoin", "VOO"}

    async def test_get_asset_foreign_user_404(self, client: AsyncClient, test_password: str):
        token_a = await self._register_and_login(client, "inv_fr1@test.com", test_password)
        token_b = await self._register_and_login(client, "inv_fr2@test.com", test_password)
        asset = await self._create_asset(client, token_a)
        resp = await client.get(
            f"/api/v1/investments/assets/{asset['id']}",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert resp.status_code == 404

    async def test_update_asset_price(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "inv_up1@test.com", test_password)
        asset = await self._create_asset(client, token, current_price=100)
        resp = await client.patch(
            f"/api/v1/investments/assets/{asset['id']}",
            json={"current_price": 120},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["current_price"] == 120.0

    async def test_create_and_get_portfolio(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "inv_pf1@test.com", test_password)
        portfolio = await self._create_portfolio(client, token)
        resp = await client.get(
            f"/api/v1/investments/portfolios/{portfolio['id']}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Portafolio Principal"
        assert data["asset_count"] == 0


@pytest.mark.api
class TestInvestmentTransactions:
    async def _setup(
        self, client: AsyncClient, email: str, test_password: str
    ) -> tuple[str, dict, dict]:
        await client.post(
            "/api/v1/auth/register", json={"email": email, "password": test_password}
        )
        login = await client.post(
            "/api/v1/auth/login", json={"email": email, "password": test_password}
        )
        access = login.json()["tokens"]["access_token"]
        asset_resp = await client.post(
            "/api/v1/investments/assets",
            json={"name": "TSLA", "asset_type": "stock", "symbol": "TSLA", "current_price": 200},
            headers={"Authorization": f"Bearer {access}"},
        )
        portfolio_resp = await client.post(
            "/api/v1/investments/portfolios",
            json={"name": "Principal"},
            headers={"Authorization": f"Bearer {access}"},
        )
        return access, asset_resp.json(), portfolio_resp.json()

    async def test_buy_updates_holdings(self, client: AsyncClient, test_password: str):
        token, asset, portfolio = await self._setup(
            client, "inv_buy1@test.com", test_password
        )
        resp = await client.post(
            f"/api/v1/investments/assets/{asset['id']}/transactions",
            json={
                "type": "buy",
                "quantity": 10,
                "price_per_unit": 100,
                "fees": 5,
                "portfolio_id": portfolio["id"],
                "date": _iso(),
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["type"] == "buy"
        assert data["total_amount"] == 1005.0  # 10 * 100 + 5

        portfolio_detail = await client.get(
            f"/api/v1/investments/portfolios/{portfolio['id']}",
            headers={"Authorization": f"Bearer {token}"},
        )
        pa = portfolio_detail.json()["assets"][0]
        assert pa["quantity"] == 10.0
        assert pa["cost_basis"] == 1005.0
        assert pa["average_price"] == 100.5

    async def test_second_buy_recalculates_average_price(
        self, client: AsyncClient, test_password: str
    ):
        token, asset, portfolio = await self._setup(
            client, "inv_buy2@test.com", test_password
        )
        for price, qty in [(100, 10), (200, 10)]:
            resp = await client.post(
                f"/api/v1/investments/assets/{asset['id']}/transactions",
                json={
                    "type": "buy",
                    "quantity": qty,
                    "price_per_unit": price,
                    "fees": 0,
                    "portfolio_id": portfolio["id"],
                    "date": _iso(),
                },
                headers={"Authorization": f"Bearer {token}"},
            )
            assert resp.status_code == 201, resp.text

        portfolio_detail = await client.get(
            f"/api/v1/investments/portfolios/{portfolio['id']}",
            headers={"Authorization": f"Bearer {token}"},
        )
        pa = portfolio_detail.json()["assets"][0]
        assert pa["quantity"] == 20.0
        assert pa["cost_basis"] == 3000.0  # 1000 + 2000
        assert pa["average_price"] == 150.0

    async def test_sell_reduces_holdings(self, client: AsyncClient, test_password: str):
        token, asset, portfolio = await self._setup(
            client, "inv_sel1@test.com", test_password
        )
        buy = await client.post(
            f"/api/v1/investments/assets/{asset['id']}/transactions",
            json={"type": "buy", "quantity": 20, "price_per_unit": 50, "fees": 0,
                  "portfolio_id": portfolio["id"], "date": _iso()},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert buy.status_code == 201
        sell = await client.post(
            f"/api/v1/investments/assets/{asset['id']}/transactions",
            json={"type": "sell", "quantity": 8, "price_per_unit": 60, "fees": 2,
                  "portfolio_id": portfolio["id"], "date": _iso()},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert sell.status_code == 201, sell.text

        portfolio_detail = await client.get(
            f"/api/v1/investments/portfolios/{portfolio['id']}",
            headers={"Authorization": f"Bearer {token}"},
        )
        pa = portfolio_detail.json()["assets"][0]
        assert pa["quantity"] == 12.0
        # cost_basis 1000, ratio 8/20=0.4 => remaining 600, avg 50
        assert pa["cost_basis"] == 600.0
        assert pa["average_price"] == 50.0

    async def test_cannot_sell_more_than_held(self, client: AsyncClient, test_password: str):
        token, asset, portfolio = await self._setup(
            client, "inv_sel2@test.com", test_password
        )
        buy = await client.post(
            f"/api/v1/investments/assets/{asset['id']}/transactions",
            json={"type": "buy", "quantity": 5, "price_per_unit": 50, "fees": 0,
                  "portfolio_id": portfolio["id"], "date": _iso()},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert buy.status_code == 201
        sell = await client.post(
            f"/api/v1/investments/assets/{asset['id']}/transactions",
            json={"type": "sell", "quantity": 50, "price_per_unit": 60, "fees": 0,
                  "portfolio_id": portfolio["id"], "date": _iso()},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert sell.status_code == 422

    async def test_transaction_updates_asset_price(self, client: AsyncClient, test_password: str):
        token, asset, portfolio = await self._setup(
            client, "inv_price1@test.com", test_password
        )
        resp = await client.post(
            f"/api/v1/investments/assets/{asset['id']}/transactions",
            json={"type": "buy", "quantity": 1, "price_per_unit": 333, "fees": 0,
                  "portfolio_id": portfolio["id"], "date": _iso()},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        asset_detail = await client.get(
            f"/api/v1/investments/assets/{asset['id']}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert asset_detail.json()["current_price"] == 333.0


@pytest.mark.api
class TestPortfolioSummary:
    async def test_summary_computes_value_and_gain(self, client: AsyncClient, test_password: str):
        await client.post(
            "/api/v1/auth/register", json={"email": "inv_sm1@test.com", "password": test_password}
        )
        login = await client.post(
            "/api/v1/auth/login", json={"email": "inv_sm1@test.com", "password": test_password}
        )
        access = login.json()["tokens"]["access_token"]

        asset = await client.post(
            "/api/v1/investments/assets",
            json={"name": "MSFT", "asset_type": "stock", "current_price": 300},
            headers={"Authorization": f"Bearer {access}"},
        )
        asset_id = asset.json()["id"]
        portfolio = await client.post(
            "/api/v1/investments/portfolios",
            json={"name": "Principal"},
            headers={"Authorization": f"Bearer {access}"},
        )
        portfolio_id = portfolio.json()["id"]

        buy = await client.post(
            f"/api/v1/investments/assets/{asset_id}/transactions",
            json={"type": "buy", "quantity": 4, "price_per_unit": 100, "fees": 0,
                  "portfolio_id": portfolio_id, "date": _iso()},
            headers={"Authorization": f"Bearer {access}"},
        )
        assert buy.status_code == 201

        summary = await client.get(
            "/api/v1/investments/portfolio", headers={"Authorization": f"Bearer {access}"}
        )
        assert summary.status_code == 200
        data = summary.json()
        # market value uses current_price (updated to last tx price = 100) * 4
        assert data["total_value"] == 400.0
        assert data["total_cost"] == 400.0
        assert data["gain_loss"] == 0.0
        assert data["asset_count"] == 1
        assert data["portfolio_count"] == 1
        assert data["asset_allocation"]["stock"] == 400.0

    async def test_summary_empty(self, client: AsyncClient, test_password: str):
        await client.post(
            "/api/v1/auth/register", json={"email": "inv_sm2@test.com", "password": test_password}
        )
        login = await client.post(
            "/api/v1/auth/login", json={"email": "inv_sm2@test.com", "password": test_password}
        )
        access = login.json()["tokens"]["access_token"]
        summary = await client.get(
            "/api/v1/investments/portfolio", headers={"Authorization": f"Bearer {access}"}
        )
        assert summary.status_code == 200
        data = summary.json()
        assert data["total_value"] == 0.0
        assert data["total_cost"] == 0.0
        assert data["gain_loss"] == 0.0
        assert data["gain_loss_percent"] == 0.0
        assert data["asset_count"] == 0


@pytest.mark.api
class TestPriceHistory:
    async def test_add_and_get_price_points(self, client: AsyncClient, test_password: str):
        await client.post(
            "/api/v1/auth/register", json={"email": "inv_ph1@test.com", "password": test_password}
        )
        login = await client.post(
            "/api/v1/auth/login", json={"email": "inv_ph1@test.com", "password": test_password}
        )
        access = login.json()["tokens"]["access_token"]
        asset = await client.post(
            "/api/v1/investments/assets",
            json={"name": "BTC", "asset_type": "crypto", "current_price": 100},
            headers={"Authorization": f"Bearer {access}"},
        )
        asset_id = asset.json()["id"]

        today = datetime.now(UTC).date().isoformat()
        resp = await client.post(
            f"/api/v1/investments/assets/{asset_id}/price-history",
            json={"close_price": 120, "date": today, "open_price": 115, "high_price": 125, "low_price": 110},
            headers={"Authorization": f"Bearer {access}"},
        )
        assert resp.status_code == 201
        assert resp.json()["close_price"] == 120.0

        # upsert same date updates
        resp2 = await client.post(
            f"/api/v1/investments/assets/{asset_id}/price-history",
            json={"close_price": 130, "date": today},
            headers={"Authorization": f"Bearer {access}"},
        )
        assert resp2.status_code == 201

        hist = await client.get(
            f"/api/v1/investments/assets/{asset_id}/price-history",
            headers={"Authorization": f"Bearer {access}"},
        )
        assert hist.status_code == 200
        points = hist.json()["points"]
        assert len(points) == 1
        assert points[0]["close_price"] == 130.0

        asset_detail = await client.get(
            f"/api/v1/investments/assets/{asset_id}",
            headers={"Authorization": f"Bearer {access}"},
        )
        assert asset_detail.json()["current_price"] == 130.0

    async def test_price_history_foreign_asset_404(self, client: AsyncClient, test_password: str):
        await client.post(
            "/api/v1/auth/register", json={"email": "inv_ph2@test.com", "password": test_password}
        )
        login_a = await client.post(
            "/api/v1/auth/login", json={"email": "inv_ph2@test.com", "password": test_password}
        )
        access_a = login_a.json()["tokens"]["access_token"]
        await client.post(
            "/api/v1/auth/register", json={"email": "inv_ph3@test.com", "password": test_password}
        )
        login_b = await client.post(
            "/api/v1/auth/login", json={"email": "inv_ph3@test.com", "password": test_password}
        )
        access_b = login_b.json()["tokens"]["access_token"]
        asset = await client.post(
            "/api/v1/investments/assets",
            json={"name": "ETH", "asset_type": "crypto"},
            headers={"Authorization": f"Bearer {access_a}"},
        )
        resp = await client.get(
            f"/api/v1/investments/assets/{asset.json()['id']}/price-history",
            headers={"Authorization": f"Bearer {access_b}"},
        )
        assert resp.status_code == 404


@pytest.mark.api
class TestDeleteOperations:
    async def test_delete_asset_and_portfolio(self, client: AsyncClient, test_password: str):
        await client.post(
            "/api/v1/auth/register", json={"email": "inv_del1@test.com", "password": test_password}
        )
        login = await client.post(
            "/api/v1/auth/login", json={"email": "inv_del1@test.com", "password": test_password}
        )
        access = login.json()["tokens"]["access_token"]
        asset = await client.post(
            "/api/v1/investments/assets",
            json={"name": "GOOG", "asset_type": "stock", "symbol": "GOOG"},
            headers={"Authorization": f"Bearer {access}"},
        )
        asset_id = asset.json()["id"]
        portfolio = await client.post(
            "/api/v1/investments/portfolios",
            json={"name": "Temporal"},
            headers={"Authorization": f"Bearer {access}"},
        )
        portfolio_id = portfolio.json()["id"]

        del_resp = await client.delete(
            f"/api/v1/investments/assets/{asset_id}",
            headers={"Authorization": f"Bearer {access}"},
        )
        assert del_resp.status_code == 200
        assert del_resp.json()["status"] == "deleted"

        # asset no longer visible
        get_resp = await client.get(
            f"/api/v1/investments/assets/{asset_id}",
            headers={"Authorization": f"Bearer {access}"},
        )
        assert get_resp.status_code == 404

        del_pf = await client.delete(
            f"/api/v1/investments/portfolios/{portfolio_id}",
            headers={"Authorization": f"Bearer {access}"},
        )
        assert del_pf.status_code == 200

        get_pf = await client.get(
            f"/api/v1/investments/portfolios/{portfolio_id}",
            headers={"Authorization": f"Bearer {access}"},
        )
        assert get_pf.status_code == 404

    async def test_delete_foreign_asset_404(self, client: AsyncClient, test_password: str):
        await client.post(
            "/api/v1/auth/register", json={"email": "inv_del2@test.com", "password": test_password}
        )
        login_a = await client.post(
            "/api/v1/auth/login", json={"email": "inv_del2@test.com", "password": test_password}
        )
        access_a = login_a.json()["tokens"]["access_token"]
        await client.post(
            "/api/v1/auth/register", json={"email": "inv_del3@test.com", "password": test_password}
        )
        login_b = await client.post(
            "/api/v1/auth/login", json={"email": "inv_del3@test.com", "password": test_password}
        )
        access_b = login_b.json()["tokens"]["access_token"]
        asset = await client.post(
            "/api/v1/investments/assets",
            json={"name": "NFLX", "asset_type": "stock"},
            headers={"Authorization": f"Bearer {access_a}"},
        )
        resp = await client.delete(
            f"/api/v1/investments/assets/{asset.json()['id']}",
            headers={"Authorization": f"Bearer {access_b}"},
        )
        assert resp.status_code == 404
