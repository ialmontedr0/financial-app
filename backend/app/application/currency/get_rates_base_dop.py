"""Use case: build a base-DOP rate map for all supported currencies."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from app.infrastructure.currency.exchange_rate_provider import ExchangeRateProvider
from app.domain.users.value_objects import SUPPORTED_CURRENCIES

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


DEFAULT_BASE = "DOP"


class GetRatesBaseDopUseCase:
    """Return a single rate map ``{currency: units_of_base_per_1_currency}``.

    Every rate is expressed in ``DEFAULT_BASE`` (DOP) per unit of the source
    currency, so the frontend can compose conversions without fetching pair by
    pair.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._provider = ExchangeRateProvider(session)

    async def execute(self, rate_date: date | None = None) -> dict[str, Any]:
        """Build and return the base-DOP map.

        Respects ISO 4217 codes (``CurrencyCode`` validates) and skips any
        currency for which no rate toward the base can be resolved.
        """
        base = DEFAULT_BASE
        map_rates: dict[str, float] = {}
        for code in SUPPORTED_CURRENCIES:
            if code == base:
                map_rates[base] = 1.0
                continue
            rate = await self._provider.get_rate(code, base, rate_date or date.today())  # noqa: DTZ011
            if rate is None or rate <= 0:
                continue
            map_rates[code] = float(Decimal(str(rate)).quantize(Decimal("0.000001")))
        return {
            "base": base,
            "date": (rate_date or date.today()).isoformat(),  # noqa: DTZ011
            "rates": map_rates,
        }