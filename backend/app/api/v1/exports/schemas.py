"""Schemas for export endpoints."""

from __future__ import annotations

from pydantic import BaseModel


class ExportTransactionsRequest(BaseModel):
    date_from: str | None = None
    date_to: str | None = None
    category: str | None = None
    transaction_type: str | None = None
    account_id: str | None = None


class ExportBudgetRequest(BaseModel):
    month: int | None = None
    year: int | None = None


class ExportGoalsRequest(BaseModel):
    status: str | None = None
