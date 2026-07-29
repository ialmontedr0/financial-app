from __future__ import annotations

from pydantic import BaseModel, Field


class CreateCreditPurchaseSchema(BaseModel):
    item_name: str = Field(..., min_length=1, max_length=200)
    total_price: float = Field(..., gt=0)
    store_name: str | None = Field(None, max_length=200)
    description: str | None = Field(None, max_length=500)
    down_payment: float = Field(0, ge=0)
    annual_interest_rate: float = Field(0, ge=0)
    installment_count: int = Field(1, ge=1, le=120)
    installment_frequency: str = Field(
        "monthly",
        pattern=r"^(monthly|biweekly|weekly|quarterly|quadrimensual|semestral|annual)$",
    )
    installment_amount: float | None = Field(None, gt=0)
    purchase_date: str | None = None
    first_due_date: str | None = None
    notes: str | None = Field(None, max_length=1000)


class UpdateCreditPurchaseSchema(BaseModel):
    item_name: str | None = Field(None, min_length=1, max_length=200)
    store_name: str | None = Field(None, max_length=200)
    description: str | None = Field(None, max_length=500)
    notes: str | None = Field(None, max_length=1000)
    status: str | None = Field(
        None, pattern=r"^(active|completed|cancelled)$"
    )
    annual_interest_rate: float | None = Field(None, ge=0)


class SimulateCreditPurchaseSchema(BaseModel):
    total_price: float = Field(..., gt=0)
    down_payment: float = Field(0, ge=0)
    annual_interest_rate: float = Field(0, ge=0)
    installment_count: int = Field(1, ge=1, le=120)
    installment_frequency: str = Field(
        "monthly",
        pattern=r"^(monthly|biweekly|weekly|quarterly|quadrimensual|semestral|annual)$",
    )
    installment_amount: float | None = Field(None, gt=0)
    first_due_date: str | None = None
