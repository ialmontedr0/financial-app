"""Financial API client unit tests."""

import pytest


class TestFinancialAPI:
    @pytest.mark.asyncio
    async def test_get_latest_rates(self):
        from app.integrations.financial_api_client import get_latest_rates

        result = await get_latest_rates(base="USD", symbols=["EUR", "GBP"])
        assert result["success"] is True
        assert "rates" in result
        assert "EUR" in result["rates"]

    @pytest.mark.asyncio
    async def test_get_latest_rates_default(self):
        from app.integrations.financial_api_client import get_latest_rates

        result = await get_latest_rates(base="USD")
        assert result["success"] is True
        assert len(result["rates"]) > 0

    @pytest.mark.asyncio
    async def test_get_historical_rate(self):
        from app.integrations.financial_api_client import get_historical_rate

        result = await get_historical_rate(date="2024-01-15", base="USD", target="EUR")
        assert result["success"] is True
        assert result["rate"] is not None
