"""Pydantic schemas for budget endpoints."""

from __future__ import annotations

from pydantic import BaseModel, Field


class CreateBudgetRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    amount: str = Field(..., description="Budget limit amount")
    budget_type: str = Field("total", description="total, category, account")
    period: str = Field("monthly", description="weekly, biweekly, monthly, quarterly, yearly")
    start_date: str | None = None
    end_date: str | None = None
    category_id: str | None = None
    account_id: str | None = None
    alert_threshold: int = Field(80, ge=1, le=100)
    alert_enabled: bool = True
    auto_adjust: bool = False
    rollover: bool = False
    strategy: str | None = None
    icon: str | None = None
    color: str | None = None


class BudgetResponse(BaseModel):
    id: str
    name: str
    description: str | None = None
    budget_type: str
    amount: str
    spent: str
    remaining: str
    period: str
    start_date: str
    end_date: str
    category_id: str | None = None
    account_id: str | None = None
    alert_threshold: int
    alert_enabled: bool
    auto_adjust: bool
    rollover: bool
    strategy: str | None = None
    is_active: bool
    pct_used: float
    status: str
    icon: str | None = None
    color: str | None = None
    created_at: str | None = None


class BudgetSummaryResponse(BaseModel):
    total_budgets: int
    total_budget_amount: str
    total_spent: str
    total_remaining: str
    utilization_pct: str
    over_budget_count: int
    near_limit_count: int
    unread_alerts: int
    new_alerts_triggered: int


class AutoAdjustRequest(BaseModel):
    buffer_pct: float = Field(10.0, ge=0, le=100)
    apply: bool = Field(False)


class AlertResponse(BaseModel):
    id: str
    budget_id: str
    alert_type: str
    severity: str
    title: str
    message: str
    threshold_percentage: int | None = None
    current_amount: str | None = None
    budget_amount: str | None = None
    is_read: bool
    is_dismissed: bool
    triggered_at: str | None = None


class MarkAlertReadRequest(BaseModel):
    alert_id: str | None = None
    mark_all: bool = False
