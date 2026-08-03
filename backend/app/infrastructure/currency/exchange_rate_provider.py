"""Exchange rate provider — DB-cached rates with external API fallback.

Responsibilities:
  * serve cached rates stored in ``currency_exchange_rate``
  * fall back to the most recent rate no newer than the requested date
  * derive the inverse rate when only the reversed pair is cached
  * fetch missing rates from an external provider and persist them

This class never raises for network/provider errors: ``get_rate`` returns
``None`` so callers can degrade gracefully (e.g. serve data unconverted).
"""

from __future__ import annotations

import logging
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.domain.currency.value_objects import CurrencyPair
from app.domain.users.value_objects import CurrencyCode
from app.infrastructure.models.currency_exchange_rate import CurrencyExchangeRateModel

logger = logging.getLogger(__name__)


class ExchangeRateProvider:
    """Provider of exchange rates backed by the local cache table."""

    def __init__(self, session: AsyncSession, settings: Settings | None = None) -> None:
        self._session = session
        from app.core.config import get_settings

        self._settings = settings or get_settings()

    async def get_rate(
        self,
        source: str,
        target: str,
        rate_date: date,
    ) -> Decimal | None:
        """Return the rate of 1 ``source`` unit expressed in ``target``.

        Returns ``None`` when no rate can be resolved.
        """
        pair = CurrencyPair(source, target)
        if pair.is_same_currency:
            return Decimal("1")

        cached = await self._find_cached(pair, rate_date)
        if cached is not None:
            return cached

        inverse = await self._find_cached(pair.inverse, rate_date)
        if inverse is not None:
            return (Decimal("1") / inverse).quantize(Decimal("0.00000001"))

        fetched = await self._fetch_and_store(pair, rate_date)
        return fetched

    async def _find_cached(self, pair: CurrencyPair, rate_date: date) -> Decimal | None:
        """Look for a rate for the pair on/before ``rate_date``."""
        lookback = rate_date - timedelta(days=self._settings.EXCHANGE_RATE_NEAREST_LOOKBACK_DAYS)
        stmt = (
            select(CurrencyExchangeRateModel)
            .where(
                CurrencyExchangeRateModel.source_currency == pair.source,
                CurrencyExchangeRateModel.target_currency == pair.target,
                CurrencyExchangeRateModel.rate_date <= rate_date,
                CurrencyExchangeRateModel.rate_date >= lookback,
            )
            .order_by(CurrencyExchangeRateModel.rate_date.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return row.rate if row is not None else None

    async def store_rate(
        self,
        source: str,
        target: str,
        rate: Decimal,
        rate_date: date,
    ) -> CurrencyExchangeRateModel:
        """Upsert a rate for a pair/date, returning the persisted row."""
        pair = CurrencyPair(source, target)
        value = Decimal(str(rate))
        if value <= 0:
            raise ValueError(f"Tasa de cambio invalida: {rate}. Debe ser positiva.")

        stmt = select(CurrencyExchangeRateModel).where(
            CurrencyExchangeRateModel.source_currency == pair.source,
            CurrencyExchangeRateModel.target_currency == pair.target,
            CurrencyExchangeRateModel.rate_date == rate_date,
        )
        result = await self._session.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing is not None:
            existing.rate = value
            return existing

        row = CurrencyExchangeRateModel(
            source_currency=pair.source,
            target_currency=pair.target,
            rate=value,
            rate_date=rate_date,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def list_rates(self, rate_date: date) -> list[CurrencyExchangeRateModel]:
        """List all stored rates for a given date."""
        stmt = (
            select(CurrencyExchangeRateModel)
            .where(CurrencyExchangeRateModel.rate_date == rate_date)
            .order_by(
                CurrencyExchangeRateModel.source_currency, CurrencyExchangeRateModel.target_currency
            )
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def _fetch_and_store(self, pair: CurrencyPair, rate_date: date) -> Decimal | None:
        """Fetch a rate from the external API and persist it in the cache."""
        value = await self._fetch_external(pair, rate_date)
        if value is None:
            return None
        try:
            await self.store_rate(pair.source, pair.target, value, rate_date)
            await self._session.commit()
        except Exception:  # cache write must never break the request
            await self._session.rollback()
            logger.exception("No se pudo persistir la tasa de cambio %s", pair)
        return value

    async def _fetch_external(self, pair: CurrencyPair, rate_date: date) -> Decimal | None:
        """Query the configured external exchange-rate API for a single pair."""
        params: dict[str, str | int] = {
            "from": pair.source,
            "to": pair.target,
            "date": rate_date.isoformat(),
        }
        if self._settings.EXCHANGE_RATE_API_KEY:
            params["access_key"] = self._settings.EXCHANGE_RATE_API_KEY

        try:
            async with httpx.AsyncClient(
                timeout=self._settings.EXCHANGE_RATE_FETCH_TIMEOUT_SECONDS
            ) as client:
                response = await client.get(self._settings.EXCHANGE_RATE_API_URL, params=params)
                response.raise_for_status()
                data = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            logger.warning("Fallo el fetch de tasa %s @ %s: %s", pair, rate_date, exc)
            return None

        raw = data.get("result") if isinstance(data, dict) else None
        if raw is None:
            if isinstance(data, dict) and data.get("success") is False:
                logger.warning(
                    "API de tasas reporto error para %s: %s",
                    pair,
                    data.get("error"),
                )
            return None
        try:
            return Decimal(str(raw))
        except (InvalidOperation, ValueError):
            logger.warning("Valor de tasa invalido de la API para %s: %r", pair, raw)
            return None


def validate_currency_code(code: str) -> str:
    """Normalize and validate an ISO 4217 currency code (public helper)."""
    return CurrencyCode(code).code
