"""Pydantic schemas for income endpoints."""

from __future__ import annotations

from pydantic import BaseModel, Field


class CreateIncomeRequest(BaseModel):
    account_id: str
    amount: str = Field(..., min_length=1)
    currency_code: str = "DOP"
    description: str = Field(..., min_length=1, max_length=500)
    effective_date: str
    category_id: str | None = None
    subcategory_id: str | None = None
    status: str = "pending"
    notes: str | None = None
    source: str | None = None
    tags: list[str] | None = None
    income_type: str = "salary"
    income_status: str = "pending"
    stability: str = "fixed"
    income_source_id: str | None = None
    employer_name: str | None = None
    employer_tax_id: str | None = None
    gross_amount: str | None = None
    tax_withheld: str | None = None
    net_amount: str | None = None
    frequency: str | None = None


class IncomeResponse(BaseModel):
    id: str
    transaction_id: str
    user_id: str
    account_id: str
    amount: str
    currency_code: str
    description: str
    effective_date: str
    category_id: str | None = None
    subcategory_id: str | None = None
    status: str
    notes: str | None = None
    source: str | None = None
    tags: list[str]
    income_type: str
    income_status: str
    stability: str
    income_source_id: str | None = None
    income_source_name: str | None = None
    employer_name: str | None = None
    gross_amount: str | None = None
    tax_withheld: str | None = None
    net_amount: str | None = None
    frequency: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class ListIncomesResponse(BaseModel):
    incomes: list[IncomeResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ======================================================================
# Income Sources
# ======================================================================

class CreateSourceRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    income_type: str = "salary"
    stability: str = "fixed"
    description: str | None = None
    tax_id: str | None = None
    default_amount: str | None = None
    default_account_id: str | None = None
    default_category_id: str | None = None
    frequency: str | None = None
    pay_day: int | None = None
    icon: str | None = None
    color: str | None = None


class SourceResponse(BaseModel):
    id: str
    name: str
    income_type: str
    stability: str
    description: str | None = None
    tax_id: str | None = None
    default_amount: str | None = None
    default_account_id: str | None = None
    default_category_id: str | None = None
    frequency: str | None = None
    pay_day: int | None = None
    total_received: str
    income_count: int
    last_received_at: str | None = None
    is_active: bool
    created_at: str | None = None


class ListSourcesResponse(BaseModel):
    sources: list[SourceResponse]
    total: int


# ======================================================================
# Income Schedule
# ======================================================================

class CreateScheduleRequest(BaseModel):
    description: str = Field(..., min_length=1, max_length=500)
    amount: str
    account_id: str
    expected_date: str
    income_source_id: str | None = None
    currency_code: str = "DOP"
    frequency: str | None = None
    projection_method: str | None = None
    confidence_score: float | None = None
    notes: str | None = None


class ScheduleResponse(BaseModel):
    id: str
    description: str
    amount: str
    currency_code: str
    account_id: str
    income_source_id: str | None = None
    expected_date: str
    status: str
    frequency: str | None = None
    projection_method: str | None = None
    confidence_score: str | None = None
    received_at: str | None = None
    created_at: str | None = None


class ListScheduleResponse(BaseModel):
    schedules: list[ScheduleResponse]
    total: int


class ReceiveScheduledRequest(BaseModel):
    received_date: str | None = None
    amount: str | None = None
    notes: str | None = None
    tags: list[str] | None = None


# ======================================================================
# Analytics
# ======================================================================

class IncomeSummaryResponse(BaseModel):
    period_start: str
    period_end: str
    total_income: str
    total_count: int
    average_monthly_income: str
    gross_income: str
    total_tax_withheld: str
    net_income: str
    by_type: list[dict]
    by_stability: list[dict]
    by_source: list[dict]


class IncomeTrendsResponse(BaseModel):
    monthly_data: list[dict]
    trend: str
    average_monthly: str
    period_months: int


class IncomeForecastResponse(BaseModel):
    average_monthly_3m: str
    average_monthly_6m: str
    average_monthly_12m: str
    trend: str
    projected_next_6m: str
    projected_monthly: str


class IncomeBySourceResponse(BaseModel):
    by_source: list[dict]
    period_start: str
    period_end: str


class IncomeByCategoryResponse(BaseModel):
    by_category: list[dict]
    period_start: str
    period_end: str


class MonthlyBreakdownResponse(BaseModel):
    year: int
    month: int
    total: str
    count: int
    incomes: list[dict]


class RecurringCandidatesResponse(BaseModel):
    total_candidates: int
    monthly_like_count: int
    estimated_monthly_recurring: str
    candidates: list[dict]


class IrregularIncomeResponse(BaseModel):
    irregularity_count: int
    irregularities: list[dict]
    period_months: int


class ProjectedIncomeResponse(BaseModel):
    total_projected: str
    months: int
    monthly_breakdown: dict
    schedule_count: int


class BatchUpdateStatusRequest(BaseModel):
    income_ids: list[str]
    status: str


class BatchUpdateStatusResponse(BaseModel):
    updated: int
    errors: int
    error_details: list[dict]
