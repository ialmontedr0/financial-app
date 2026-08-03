"""Tests for the CurrencyConversionMiddleware (X-Currency header)."""

from datetime import date
from decimal import Decimal

import pytest
from httpx import AsyncClient

from app.infrastructure.currency.exchange_rate_provider import ExchangeRateProvider


@pytest.mark.api
class TestCurrencyConversionMiddleware:
    async def _setup(self, client: AsyncClient, email: str, password: str) -> tuple[str, str]:
        await client.post("/api/v1/auth/register", json={"email": email, "password": password})
        login_resp = await client.post(
            "/api/v1/auth/login", json={"email": email, "password": password}
        )
        token = login_resp.json()["tokens"]["access_token"]
        acc_resp = await client.post(
            "/api/v1/accounts",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "Cuenta DOP",
                "account_type": "checking",
                "currency_code": "DOP",
                "initial_balance": 50000,
            },
        )
        account_id = acc_resp.json()["id"]
        await client.post(
            "/api/v1/transactions",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "account_id": account_id,
                "transaction_type": "expense",
                "amount": 100,
                "description": "Compra",
                "effective_date": "2026-07-19",
            },
        )
        return token, account_id

    async def test_list_without_header_is_unchanged(self, client: AsyncClient, test_password: str):
        token, _ = await self._setup(client, "mwx0@test.com", test_password)
        response = await client.get(
            "/api/v1/transactions",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        tx = response.json()["transactions"][0]
        assert tx["amount"] == "100.0000"
        assert tx["currency_code"] == "DOP"
        assert "X-Converted" not in response.headers

    async def test_list_converts_with_x_currency(
        self, client: AsyncClient, db_session, test_password: str
    ):
        token, _ = await self._setup(client, "mwx1@test.com", test_password)

        provider = ExchangeRateProvider(db_session)
        await provider.store_rate("DOP", "USD", Decimal("0.0177"), date.today())  # noqa: DTZ011
        await db_session.commit()

        response = await client.get(
            "/api/v1/transactions",
            headers={"Authorization": f"Bearer {token}", "X-Currency": "USD"},
        )
        assert response.status_code == 200
        tx = response.json()["transactions"][0]
        assert tx["amount"] == "1.7700"
        assert tx["original_currency"] == "DOP"
        assert response.headers["X-Converted"] == "DOP->USD"

    async def test_list_same_currency_is_unchanged(self, client: AsyncClient, test_password: str):
        token, _ = await self._setup(client, "mwx2@test.com", test_password)
        response = await client.get(
            "/api/v1/transactions",
            headers={"Authorization": f"Bearer {token}", "X-Currency": "DOP"},
        )
        assert response.status_code == 200
        tx = response.json()["transactions"][0]
        assert tx["amount"] == "100.0000"
        assert "X-Converted" not in response.headers

    async def test_invalid_target_header_ignored(self, client: AsyncClient, test_password: str):
        token, _ = await self._setup(client, "mwx3@test.com", test_password)
        response = await client.get(
            "/api/v1/transactions",
            headers={"Authorization": f"Bearer {token}", "X-Currency": "NOTACODE"},
        )
        assert response.status_code == 200
        assert response.json()["transactions"][0]["amount"] == "100.0000"

    async def test_accounts_list_converts_balance(
        self, client: AsyncClient, db_session, test_password: str
    ):
        token, _ = await self._setup(client, "mwx4@test.com", test_password)

        provider = ExchangeRateProvider(db_session)
        await provider.store_rate("DOP", "USD", Decimal("0.0177"), date.today())  # noqa: DTZ011
        await db_session.commit()

        response = await client.get(
            "/api/v1/accounts",
            headers={"Authorization": f"Bearer {token}", "X-Currency": "USD"},
        )
        assert response.status_code == 200
        acc = response.json()["accounts"][0]
        # 49900 DOP (50000 - gasto de 100) * 0.0177 = 883.2300 USD
        assert acc["balance"] == "883.2300"
