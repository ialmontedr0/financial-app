"""Pydantic schemas for Multi-Currency API."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SupportedCurrencyItem(BaseModel):
    """A single supported currency."""

    code: str = Field(description="ISO 4217 currency code")
    name: str = Field(description="Human readable currency name")


class SupportedCurrenciesResponse(BaseModel):
    """List of supported currencies."""

    currencies: list[SupportedCurrencyItem]
    total: int


class ConvertCurrencyResponse(BaseModel):
    """Result of a currency conversion."""

    amount: str
    from_currency: str
    to_currency: str
    rate: str
    converted_amount: str
    date: str


class ExchangeRateItem(BaseModel):
    """A stored exchange rate for a pair/date."""

    source_currency: str
    target_currency: str
    rate: str
    rate_date: str


class ListExchangeRatesResponse(BaseModel):
    """Stored rates for a given date."""

    rates: list[ExchangeRateItem]
    total: int
    date: str
