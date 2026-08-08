"""Currency API router - multi-currency conversion and rates."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING, Any

import structlog
from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_active_user, get_db
from app.api.v1.currency.schemas import (
    BaseDopRatesResponse,
    ConvertCurrencyResponse,
    ListExchangeRatesResponse,
    SupportedCurrenciesResponse,
)
from app.application.currency.convert_currency import ConvertCurrencyUseCase
from app.application.currency.get_rates_base_dop import GetRatesBaseDopUseCase
from app.application.currency.list_exchange_rates import ListExchangeRatesUseCase
from app.application.currency.list_supported_currencies import GetSupportedCurrenciesUseCase

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()

router = APIRouter(prefix="/currency", tags=["Multi-Currency"])


# ============================================================
# Supported Currencies
# ============================================================


@router.get(
    "/supported",
    response_model=SupportedCurrenciesResponse,
    summary="List supported currencies",
    description="Returns all ISO 4217 currencies the platform supports.",
)
async def list_supported_currencies(
    current_user: dict[str, Any] = Depends(get_current_active_user),
) -> dict[str, Any]:
    """List supported currency codes with human labels."""
    use_case = GetSupportedCurrenciesUseCase()
    currencies = await use_case.execute()
    return {"currencies": currencies, "total": len(currencies)}


# ============================================================
# Convert Amount
# ============================================================


@router.get(
    "/convert",
    response_model=ConvertCurrencyResponse,
    summary="Convert an amount between currencies",
    description="Converts an amount using the latest stored or fetched exchange rate.",
)
async def convert_currency(
    amount: float = Query(..., gt=0, description="Amount to convert"),
    from_currency: str = Query(..., min_length=3, max_length=3, description="Source ISO 4217 code"),
    to_currency: str = Query(..., min_length=3, max_length=3, description="Target ISO 4217 code"),
    conversion_date: date | None = Query(None, alias="date", description="Conversion date"),
    current_user: dict[str, Any] = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Convert an amount from one currency to another."""
    use_case = ConvertCurrencyUseCase(db)
    return await use_case.execute(amount, from_currency, to_currency, conversion_date)


# ============================================================
# Stored Rates
# ============================================================


@router.get(
    "/rates",
    response_model=ListExchangeRatesResponse,
    summary="List stored exchange rates",
    description="Returns the exchange rates cached in the database for a given date.",
)
async def list_exchange_rates(
    rate_date: date = Query(..., alias="date", description="Date of the rates"),
    current_user: dict[str, Any] = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """List locally cached exchange rates for a date."""
    use_case = ListExchangeRatesUseCase(db)
    return await use_case.execute(rate_date)


@router.get(
    "/rates/base",
    response_model=BaseDopRatesResponse,
    summary="List base-DOP rate map",
    description="Returns a single map of rates expressed in DOP per unit of each currency.",
)
async def list_base_dop_rates(
    rate_date: date | None = Query(None, alias="date", description="Date of the rates"),
    current_user: dict[str, Any] = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """List base-DOP rate map for conversion in the frontend."""
    use_case = GetRatesBaseDopUseCase(db)
    return await use_case.execute(rate_date)
