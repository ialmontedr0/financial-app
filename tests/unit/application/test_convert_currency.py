"""Unit tests for ConvertCurrencyUseCase with a stubbed provider."""

from datetime import date
from decimal import Decimal

import pytest

from app.application.currency.convert_currency import ConvertCurrencyUseCase
from app.middleware.error_handler import CurrencyConversionError, ValidationError


class StubProvider:
    """Fake rate provider returning predetermined rates."""

    def __init__(self, rates: dict[tuple[str, str], Decimal] | None = None) -> None:
        self.rates = rates or {}

    async def get_rate(self, source: str, target: str, _rate_date: date) -> Decimal | None:
        return self.rates.get((source, target))


@pytest.mark.unit
class TestConvertCurrencyUseCase:
    async def test_same_currency_is_passthrough(self):
        provider = StubProvider()
        use_case = ConvertCurrencyUseCase(None, provider)  # type: ignore[arg-type]
        result = await use_case.execute(100, "DOP", "dop", date(2026, 1, 1))
        assert result["converted_amount"] == "100.0000"
        assert result["rate"] == "1"
        assert result["from_currency"] == "DOP"

    async def test_converts_with_rate(self):
        provider = StubProvider({("USD", "DOP"): Decimal("56.5")})
        use_case = ConvertCurrencyUseCase(None, provider)  # type: ignore[arg-type]
        result = await use_case.execute("10", "USD", "DOP", date(2026, 1, 1))
        assert result["converted_amount"] == "565.0000"
        assert result["rate"] == "56.5"
        assert result["to_currency"] == "DOP"
        assert result["date"] == "2026-01-01"

    async def test_defaults_date_to_today(self):
        provider = StubProvider({("USD", "EUR"): Decimal("0.9")})
        use_case = ConvertCurrencyUseCase(None, provider)  # type: ignore[arg-type]
        result = await use_case.execute(10, "USD", "EUR")
        assert result["date"] == date.today().isoformat()  # noqa: DTZ011

    async def test_raises_when_rate_unavailable(self):
        provider = StubProvider()
        use_case = ConvertCurrencyUseCase(None, provider)  # type: ignore[arg-type]
        with pytest.raises(CurrencyConversionError):
            await use_case.execute(10, "USD", "DOP", date(2026, 1, 1))

    async def test_invalid_currency_raises(self):
        provider = StubProvider()
        use_case = ConvertCurrencyUseCase(None, provider)  # type: ignore[arg-type]
        with pytest.raises(ValidationError):
            await use_case.execute(10, "USD", "ZZZ", date(2026, 1, 1))
