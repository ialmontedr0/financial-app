"""Plaid API schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class CreateLinkTokenSchema(BaseModel):
    redirect_uri: str | None = Field(None, max_length=500)


class ExchangeTokenSchema(BaseModel):
    public_token: str = Field(..., min_length=1, max_length=1000)


class PlaidTransactionsParamsSchema(BaseModel):
    start_date: str = Field(..., description="ISO date, e.g. 2026-01-01")
    end_date: str = Field(..., description="ISO date, e.g. 2026-07-31")


class PlaidItemSchema(BaseModel):
    id: str
    item_id: str
    institution_id: str | None = None
    institution_name: str | None = None
    status: str
    last_sync_at: str | None = None
    created_at: str | None = None


class PlaidTransactionSchema(BaseModel):
    transaction_id: str
    name: str | None = None
    merchant_name: str | None = None
    amount: float | None = None
    amount_decimal: str | None = None
    currency_code: str | None = None
    date: str | None = None
    datetime: str | None = None
    category: str | None = None
    category_id: str | None = None
    account_id: str | None = None
    pending: bool = False
    payment_channel: str | None = None
    logo_url: str | None = None
