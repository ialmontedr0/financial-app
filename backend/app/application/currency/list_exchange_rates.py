"""Use case: List stored exchange rates for a date."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING, Any

from app.infrastructure.currency.exchange_rate_provider import ExchangeRateProvider

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class ListExchangeRatesUseCase:
    """Return the locally cached rates stored for a given date."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._provider = ExchangeRateProvider(session)

    async def execute(self, rate_date: date) -> dict[str, Any]:
        """List stored rates for the date as a dict payload."""
        rows = await self._provider.list_rates(rate_date)
        rates = [
            {
                "source_currency": r.source_currency,
                "target_currency": r.target_currency,
                "rate": str(r.rate),
                "rate_date": r.rate_date.isoformat(),
            }
            for r in rows
        ]
        return {"rates": rates, "total": len(rates), "date": rate_date.isoformat()}
