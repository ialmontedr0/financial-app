"""Schemas for financial data endpoints."""

from __future__ import annotations

from pydantic import BaseModel


class ExchangeRateResponse(BaseModel):
    success: bool
    base: str
    date: str
    rates: dict[str, float]


class ExchangeRateRequest(BaseModel):
    base: str = "USD"
    target: str = "DOP"


class HistoricalRateResponse(BaseModel):
    success: bool
    date: str
    base: str
    target: str
    rate: float | None = None


class DateRangeRatesResponse(BaseModel):
    success: bool
    base: str
    target: str
    rates: dict[str, dict[str, float]]
