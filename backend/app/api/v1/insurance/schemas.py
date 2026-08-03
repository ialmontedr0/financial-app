"""Insurance API schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class CreateInsuranceSchema(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    type: str = Field(
        "other",
        pattern=r"^(life|health|auto|home|travel|disability|other)$",
    )
    provider: str | None = Field(None, max_length=200)
    policy_number: str | None = Field(None, max_length=100)
    status: str = Field(
        "active",
        pattern=r"^(active|cancelled|expired|pending)$",
    )
    start_date: str = Field(..., description="ISO date, e.g. 2026-01-01")
    end_date: str | None = None
    coverage_amount: float | None = Field(None, ge=0)
    premium_amount: float = Field(..., gt=0)
    premium_frequency: str = Field(
        "monthly",
        pattern=r"^(monthly|quarterly|semi_annual|annual)$",
    )
    notes: str | None = None


class CreatePolicySchema(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    coverage_details: str | None = None
    deductible: float | None = Field(None, ge=0)


class CreatePremiumSchema(BaseModel):
    amount: float = Field(..., gt=0)
    due_date: str = Field(..., description="ISO date, e.g. 2026-03-15")
    paid_date: str | None = None
    payment_method: str | None = Field(
        None,
        pattern=r"^(bank_transfer|cash|auto_debit|check|online|mobile)$",
    )


class MarkPremiumPaidSchema(BaseModel):
    paid_date: str | None = None
    payment_method: str | None = Field(
        None,
        pattern=r"^(bank_transfer|cash|auto_debit|check|online|mobile)$",
    )
