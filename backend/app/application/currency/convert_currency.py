"""Use case: Convert an amount between currencies.

This is the durable conversion service for the multi-currency feature. It
uses the domain ``Money`` value object for the pure arithmetic and an
``ExchangeRateProvider`` for rate resolution/caching.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from app.domain.currency.value_objects import Money, format_rate, round_money
from app.domain.users.value_objects import CurrencyCode
from app.infrastructure.currency.exchange_rate_provider import ExchangeRateProvider
from app.middleware.error_handler import CurrencyConversionError, ValidationError

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class ConvertCurrencyUseCase:
    """Convert monetary amounts between supported currencies."""

    def __init__(
        self,
        session: AsyncSession,
        provider: ExchangeRateProvider | None = None,
    ) -> None:
        self._session = session
        self._provider = provider or ExchangeRateProvider(session)

    async def execute(
        self,
        amount: Decimal | float | str,
        from_currency: str,
        to_currency: str,
        rate_date: date | None = None,
    ) -> dict[str, Any]:
        """Convert ``amount`` from ``from_currency`` to ``to_currency``.

        Returns a dictionary with the original amount, the resolved rate and
        the converted amount rounded to 4 decimal places.
        """
        conversion_date = rate_date or date.today()  # noqa: DTZ011
        try:
            money = Money(amount=Decimal(str(amount)), currency=from_currency)
            target = CurrencyCode(to_currency).code
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc

        if money.currency == target:
            return {
                "amount": str(money.amount),
                "from_currency": money.currency,
                "to_currency": target,
                "rate": "1",
                "converted_amount": str(round_money(money.amount)),
                "date": conversion_date.isoformat(),
            }

        rate = await self._provider.get_rate(money.currency, target, conversion_date)
        if rate is None:
            raise CurrencyConversionError(
                f"No se pudo obtener la tasa de cambio "
                f"{money.currency}->{target} para {conversion_date.isoformat()}"
            )

        converted = money.convert(rate, target)
        return {
            "amount": str(money.amount),
            "from_currency": money.currency,
            "to_currency": target,
            "rate": format_rate(rate),
            "converted_amount": str(converted.amount),
            "date": conversion_date.isoformat(),
        }
