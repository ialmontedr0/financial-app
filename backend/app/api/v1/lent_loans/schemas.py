"""Lent loan API schemas (préstamo otorgado)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SimulateLentLoanSchema(BaseModel):
    principal_amount: float = Field(..., gt=0)
    annual_interest_rate: float = Field(..., ge=0)
    term_months: int = Field(..., gt=0, le=600)
    start_date: str | None = None


class CreateLentLoanSchema(BaseModel):
    borrower_name: str = Field(..., min_length=1, max_length=200)
    principal_amount: float = Field(..., gt=0)
    annual_interest_rate: float = Field(..., ge=0)
    term_months: int = Field(..., gt=0, le=600)
    payment_frequency: str = Field("monthly", pattern=r"^(monthly|bi_weekly|weekly)$")
    currency_code: str = Field("DOP", min_length=3, max_length=3)
    account_id: str | None = None
    start_date: str | None = None
    is_collateralized: bool = False
    notes: str | None = Field(None, max_length=1000)


class RecordLentLoanPaymentSchema(BaseModel):
    amount: float = Field(..., gt=0)
    received_date: str | None = None
    payment_method: str = Field(
        "bank_transfer",
        pattern=r"^(bank_transfer|cash|auto_debit|check|online|mobile)$",
    )
    reference_number: str | None = Field(None, max_length=100)
    notes: str | None = Field(None, max_length=1000)