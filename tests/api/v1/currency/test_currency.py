"""Tests for the multi-currency API endpoints."""

from datetime import date
from decimal import Decimal

import pytest
from httpx import AsyncClient

from app.infrastructure.currency.exchange_rate_provider import ExchangeRateProvider


@pytest.mark.api
class TestCurrencyEndpoints:
    async def _register_and_login(self, client: AsyncClient, email: str, password: str) -> str:
        await client.post("/api/v1/auth/register", json={"email": email, "password": password})
        login_resp = await client.post(
            "/api/v1/auth/login", json={"email": email, "password": password}
        )
        return login_resp.json()["tokens"]["access_token"]

    async def test_supported_requires_auth(self, client: AsyncClient):
        response = await client.get(
            "/api/v1/currency/supported",
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        assert response.status_code == 401

    async def test_supported_currencies(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "currency@test.com", test_password)
        response = await client.get(
            "/api/v1/currency/supported",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        codes = {c["code"] for c in data["currencies"]}
        assert {"DOP", "USD", "EUR", "MXN", "VES"} <= codes
        assert data["total"] == len(data["currencies"])

    async def test_convert_same_currency(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "currency2@test.com", test_password)
        response = await client.get(
            "/api/v1/currency/convert",
            params={"amount": 100, "from_currency": "DOP", "to_currency": "DOP"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.json()["converted_amount"] == "100.0000"
        assert response.json()["rate"] == "1"

    async def test_convert_uses_seeded_rate(
        self, client: AsyncClient, db_session, test_password: str
    ):
        token = await self._register_and_login(client, "currency3@test.com", test_password)
        provider = ExchangeRateProvider(db_session)
        await provider.store_rate("USD", "DOP", Decimal("56.5"), date(2026, 1, 2))
        await db_session.commit()

        response = await client.get(
            "/api/v1/currency/convert",
            params={
                "amount": 10,
                "from_currency": "USD",
                "to_currency": "DOP",
                "date": "2026-01-02",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["converted_amount"] == "565.0000"
        assert data["rate"] == "56.5"

    async def test_convert_unavailable_rate(
        self, client: AsyncClient, monkeypatch, test_password: str
    ):
        token = await self._register_and_login(client, "currency4@test.com", test_password)

        async def fake_fetch(self, pair, rate_date):
            return None

        monkeypatch.setattr(ExchangeRateProvider, "_fetch_external", fake_fetch)

        response = await client.get(
            "/api/v1/currency/convert",
            params={
                "amount": 10,
                "from_currency": "USD",
                "to_currency": "EUR",
                "date": "2026-01-02",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 502
        assert response.json()["error"]["code"] == "CURRENCY_RATE_UNAVAILABLE"

    async def test_convert_invalid_currency(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "currency5@test.com", test_password)
        response = await client.get(
            "/api/v1/currency/convert",
            params={"amount": 10, "from_currency": "USD", "to_currency": "ZZZ"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    async def test_list_rates(self, client: AsyncClient, db_session, test_password: str):
        token = await self._register_and_login(client, "currency6@test.com", test_password)
        provider = ExchangeRateProvider(db_session)
        await provider.store_rate("EUR", "USD", Decimal("1.05"), date(2026, 1, 4))
        await db_session.commit()

        response = await client.get(
            "/api/v1/currency/rates",
            params={"date": "2026-01-04"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert any(
            r["source_currency"] == "EUR" and r["target_currency"] == "USD" for r in data["rates"]
        )
