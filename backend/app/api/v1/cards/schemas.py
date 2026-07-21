"""Pydantic schemas for credit card endpoints."""

from __future__ import annotations

from pydantic import BaseModel, Field


class UpdateCardRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    last_four_digits: str | None = None
    card_network: str | None = None
    credit_limit: str | None = None
    available_credit: str | None = None
    statement_day: int | None = Field(None, ge=1, le=28)
    payment_due_day: int | None = Field(None, ge=1, le=28)
    interest_rate: str | None = None
    is_active: bool | None = None
    include_in_totals: bool | None = None
    color: str | None = None
    icon: str | None = None


class UpdateBillRequest(BaseModel):
    total_amount: str | None = None
    minimum_payment: str | None = None
    interest_charged: str | None = None
    payment_status: str | None = Field(None, pattern=r"^(pending|partial|paid|overdue|waived)$")
    notes: str | None = None


class PayBillRequest(BaseModel):
    amount: float = Field(..., gt=0)
    payment_method: str = Field("manual", pattern=r"^(manual|auto|transfer|cash)$")


class CreateSpendingLimitRequest(BaseModel):
    limit_type: str = Field(..., pattern=r"^(daily|weekly|monthly|category)$")
    limit_amount: str = Field(..., description="Limit amount")
    category_id: str | None = None
    alert_threshold: int = Field(80, ge=1, le=100)
    alert_enabled: bool = True
    description: str | None = None


class UpdateSpendingLimitRequest(BaseModel):
    limit_amount: str | None = None
    alert_threshold: int | None = Field(None, ge=1, le=100)
    alert_enabled: bool | None = None
    description: str | None = None
    is_active: bool | None = None


class CardAlertResponse(BaseModel):
    id: str
    credit_card_id: str
    credit_card_bill_id: str | None = None
    alert_type: str
    severity: str
    title: str
    message: str
    threshold_percentage: int | None = None
    current_amount: str | None = None
    limit_amount: str | None = None
    is_read: bool
    is_dismissed: bool
    triggered_at: str | None = None


class MarkCardAlertReadRequest(BaseModel):
    alert_id: str | None = None
    mark_all: bool = False
