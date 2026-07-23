"""Financial data API tests."""

import pytest
from httpx import AsyncClient


@pytest.mark.api
class TestFinancialData:
    async def _register_and_login(
        self, client: AsyncClient, email: str, password: str
    ) -> str:
        await client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": password},
        )
        login = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
        )
        return login.json()["tokens"]["access_token"]

    async def test_exchange_rates(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "fx@test.com", test_password)
        resp = await client.get(
            "/api/v1/financial-data/exchange-rates?base=USD&symbols=EUR,GBP",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "EUR" in data["rates"]

    async def test_historical_rate(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "fx_hist@test.com", test_password)
        resp = await client.get(
            "/api/v1/financial-data/exchange-rates/EUR?date=2024-01-15&base=USD",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
