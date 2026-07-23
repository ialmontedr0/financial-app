"""Financial data API endpoints — exchange rates via Frankfurter."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_active_user
from app.api.v1.financial_data import schemas as fd_schemas

router = APIRouter(prefix="/financial-data", tags=["Financial Data"])


@router.get("/exchange-rates", response_model=fd_schemas.ExchangeRateResponse)
async def get_exchange_rates(
    base: str = Query("USD", description="Base currency"),
    symbols: str | None = Query(None, description="Comma-separated target currencies"),
    current_user: dict = Depends(get_current_active_user),
):
    """Get latest exchange rates (Frankfurter API, free, no key)."""
    from app.integrations.financial_api_client import get_latest_rates

    symbol_list = symbols.split(",") if symbols else None
    result = await get_latest_rates(base=base, symbols=symbol_list)
    return result


@router.get("/exchange-rates/{target}", response_model=fd_schemas.HistoricalRateResponse)
async def get_exchange_rate(
    target: str,
    date: str = Query("latest", description="Date (YYYY-MM-DD) or 'latest'"),
    base: str = Query("USD"),
    current_user: dict = Depends(get_current_active_user),
):
    """Get exchange rate for a specific date."""
    from app.integrations.financial_api_client import get_historical_rate, get_latest_rates

    if date == "latest":
        result = await get_latest_rates(base=base, symbols=[target])
        rate = result.get("rates", {}).get(target)
        return fd_schemas.HistoricalRateResponse(
            success=result.get("success", False),
            date=result.get("date", ""),
            base=base,
            target=target,
            rate=rate,
        )

    result = await get_historical_rate(date=date, base=base, target=target)
    return result


@router.get("/exchange-rates/range", response_model=fd_schemas.DateRangeRatesResponse)
async def get_exchange_rates_range(
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    base: str = Query("USD"),
    target: str = Query("DOP"),
    current_user: dict = Depends(get_current_active_user),
):
    """Get exchange rates for a date range."""
    from app.integrations.financial_api_client import get_date_range_rates

    result = await get_date_range_rates(
        start_date=start_date, end_date=end_date, base=base, target=target
    )
    return result
