"""Integration tests for the exchange rate provider and conversion path."""

from datetime import date, timedelta
from decimal import Decimal

import pytest

from app.application.currency.convert_currency import ConvertCurrencyUseCase
from app.infrastructure.currency.exchange_rate_provider import ExchangeRateProvider
from app.infrastructure.models.currency_exchange_rate import CurrencyExchangeRateModel
from app.middleware.error_handler import CurrencyConversionError


@pytest.mark.integration
class TestExchangeRateProvider:
    async def test_store_and_get_exact_rate(self, db_session):
        provider = ExchangeRateProvider(db_session)
        await provider.store_rate("USD", "DOP", Decimal("56.5"), date(2026, 1, 2))
        await db_session.commit()

        rate = await provider.get_rate("USD", "DOP", date(2026, 1, 2))
        assert rate == Decimal("56.5")

    async def test_same_currency_returns_one(self, db_session):
        provider = ExchangeRateProvider(db_session)
        assert await provider.get_rate("USD", "usd", date(2026, 1, 2)) == Decimal("1")

    async def test_uses_inverse_rate(self, db_session):
        provider = ExchangeRateProvider(db_session)
        await provider.store_rate("DOP", "USD", Decimal("0.0177"), date(2026, 1, 2))
        await db_session.commit()

        rate = await provider.get_rate("USD", "DOP", date(2026, 1, 2))
        assert rate is not None
        assert abs(rate - Decimal("1") / Decimal("0.0177")) < Decimal("0.00000001")

    async def test_falls_back_to_nearest_prior_date(self, db_session):
        provider = ExchangeRateProvider(db_session)
        past = date(2026, 1, 1)
        await provider.store_rate("USD", "EUR", Decimal("0.9"), past)
        await db_session.commit()

        rate = await provider.get_rate("USD", "EUR", past + timedelta(days=5))
        assert rate == Decimal("0.9")

    async def test_ignores_rates_older_than_lookback(self, db_session):
        provider = ExchangeRateProvider(db_session)
        old = date(2020, 1, 1)
        await provider.store_rate("USD", "GBP", Decimal("0.8"), old)
        await db_session.commit()

        rate = await provider.get_rate("USD", "GBP", date(2026, 1, 1))
        assert rate is None

    async def test_store_upserts_without_duplicates(self, db_session):
        provider = ExchangeRateProvider(db_session)
        await provider.store_rate("EUR", "MXN", Decimal("18.5"), date(2026, 1, 2))
        await provider.store_rate("EUR", "MXN", Decimal("19.0"), date(2026, 1, 2))
        await db_session.commit()

        from sqlalchemy import select

        result = await db_session.execute(
            select(CurrencyExchangeRateModel).where(
                CurrencyExchangeRateModel.source_currency == "EUR",
                CurrencyExchangeRateModel.target_currency == "MXN",
                CurrencyExchangeRateModel.rate_date == date(2026, 1, 2),
            )
        )
        rows = list(result.scalars().all())
        assert len(rows) == 1
        assert rows[0].rate == Decimal("19.0")

    async def test_list_rates_by_date(self, db_session):
        provider = ExchangeRateProvider(db_session)
        await provider.store_rate("JPY", "USD", Decimal("0.0067"), date(2026, 1, 3))
        await provider.store_rate("KRW", "USD", Decimal("0.00075"), date(2026, 1, 3))
        await db_session.commit()

        rows = await provider.list_rates(date(2026, 1, 3))
        codes = {(r.source_currency, r.target_currency) for r in rows}
        assert ("JPY", "USD") in codes
        assert ("KRW", "USD") in codes


@pytest.mark.integration
class TestConvertCurrencyIntegration:
    async def test_converts_using_seeded_rate(self, db_session):
        provider = ExchangeRateProvider(db_session)
        await provider.store_rate("USD", "DOP", Decimal("56.5"), date(2026, 1, 2))
        await db_session.commit()

        use_case = ConvertCurrencyUseCase(db_session, provider)
        result = await use_case.execute(10, "USD", "DOP", date(2026, 1, 2))
        assert result["converted_amount"] == "565.0000"

    async def test_raises_when_no_rate_available(self, db_session, monkeypatch):
        provider = ExchangeRateProvider(db_session)

        async def fake_fetch(self, pair, rate_date):
            return None

        monkeypatch.setattr(ExchangeRateProvider, "_fetch_external", fake_fetch)
        use_case = ConvertCurrencyUseCase(db_session, provider)
        with pytest.raises(CurrencyConversionError):
            await use_case.execute(10, "USD", "EUR", date(2026, 1, 2))
