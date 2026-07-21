"""Loan API schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class CreateLoanSchema(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    principal_amount: float = Field(..., gt=0)
    annual_interest_rate: float = Field(..., ge=0)
    term_months: int = Field(..., gt=0, le=600)
    loan_type: str = Field(
        "personal",
        pattern=r"^(personal|mortgage|auto|student|business|personal_line|payday|microloan|consolidation)$",
    )
    interest_type: str = Field("fixed", pattern=r"^(fixed|variable|mixed)$")
    payment_frequency: str = Field("monthly", pattern=r"^(monthly|bi_weekly|weekly)$")
    account_id: str | None = None
    lender_name: str | None = Field(None, max_length=200)
    account_number: str | None = Field(None, max_length=100)
    disbursement_date: str | None = None
    grace_period_days: int = Field(0, ge=0)
    early_payoff_allowed: bool = True
    early_payoff_penalty_pct: float | None = Field(None, ge=0)
    penalty_rate_monthly: float | None = Field(None, ge=0)
    notes: str | None = Field(None, max_length=1000)


class SimulateLoanSchema(BaseModel):
    principal_amount: float = Field(..., gt=0)
    annual_interest_rate: float = Field(..., ge=0)
    term_months: int = Field(..., gt=0, le=600)
    start_date: str | None = None
    extra_monthly_payment: float = Field(0, ge=0)


class MakePaymentSchema(BaseModel):
    amount: float = Field(..., gt=0)
    payment_date: str | None = None
    payment_method: str = Field(
        "bank_transfer",
        pattern=r"^(bank_transfer|cash|auto_debit|check|online|mobile)$",
    )
    reference_number: str | None = Field(None, max_length=100)
    is_extra_payment: bool = False
    notes: str | None = None
