"""External financial API client — exchange rates via Frankfurter (free, no key)."""

from __future__ import annotations

from typing import Any

import httpx
import structlog

logger = structlog.get_logger()

BASE_URL = "https://api.frankfurter.app"

SUPPORTED_CURRENCIES = {
    "DOP": "Dominican Peso",
    "USD": "US Dollar",
    "EUR": "Euro",
    "GBP": "British Pound",
    "JPY": "Japanese Yen",
    "CAD": "Canadian Dollar",
    "CHF": "Swiss Franc",
    "CNY": "Chinese Yuan",
    "MXN": "Mexican Peso",
    "BRL": "Brazilian Real",
}


async def get_latest_rates(
    base: str = "USD",
    symbols: list[str] | None = None,
) -> dict[str, Any]:
    """Get latest exchange rates from Frankfurter API."""
    params: dict[str, str] = {"base": base}
    if symbols:
        params["symbols"] = ",".join(symbols)

    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        try:
            resp = await client.get(f"{BASE_URL}/latest", params=params)
            resp.raise_for_status()
            data = resp.json()
            logger.info("exchange_rates_fetched", base=base, count=len(data.get("rates", {})))
            return {
                "success": True,
                "base": data.get("base", base),
                "date": data.get("date", ""),
                "rates": data.get("rates", {}),
            }
        except httpx.HTTPStatusError as e:
            logger.error("exchange_rates_http_error", status=e.response.status_code)
            return {"success": False, "error": f"HTTP {e.response.status_code}"}
        except httpx.RequestError as e:
            logger.error("exchange_rates_request_error", error=str(e))
            return {"success": False, "error": str(e)}


async def get_historical_rate(
    date: str,
    base: str = "USD",
    target: str = "DOP",
) -> dict[str, Any]:
    """Get historical exchange rate for a specific date."""
    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        try:
            resp = await client.get(
                f"{BASE_URL}/{date}",
                params={"base": base, "symbols": target},
            )
            resp.raise_for_status()
            data = resp.json()
            rate = data.get("rates", {}).get(target)
            return {
                "success": True,
                "date": data.get("date", date),
                "base": base,
                "target": target,
                "rate": rate,
            }
        except httpx.HTTPStatusError as e:
            return {"success": False, "error": f"HTTP {e.response.status_code}"}
        except httpx.RequestError as e:
            return {"success": False, "error": str(e)}


async def get_date_range_rates(
    start_date: str,
    end_date: str,
    base: str = "USD",
    target: str = "DOP",
) -> dict[str, Any]:
    """Get exchange rates for a date range."""
    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
        try:
            resp = await client.get(
                f"{BASE_URL}/{start_date}..{end_date}",
                params={"base": base, "symbols": target},
            )
            resp.raise_for_status()
            data = resp.json()
            return {
                "success": True,
                "base": data.get("base", base),
                "target": target,
                "rates": data.get("rates", {}),
            }
        except httpx.HTTPStatusError as e:
            return {"success": False, "error": f"HTTP {e.response.status_code}"}
        except httpx.RequestError as e:
            return {"success": False, "error": str(e)}
