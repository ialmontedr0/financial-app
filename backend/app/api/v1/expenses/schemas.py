"""Pydantic schemas for expense endpoints."""

from __future__ import annotations

from pydantic import BaseModel, Field

# ======================================================================
# Expense CRUD
# ======================================================================


class CreateExpenseRequest(BaseModel):
    account_id: str
    amount: str = Field(..., description="Monto positivo")
    currency_code: str = "DOP"
    description: str = Field(..., min_length=1, max_length=500)
    effective_date: str  # ISO date
    category_id: str | None = None
    subcategory_id: str | None = None
    status: str = "completed"
    notes: str | None = None
    source: str = "manual"
    tags: list[str] | None = None
    priority: str = "normal"
    template_id: str | None = None
    service_id: str | None = None
    subscription_id: str | None = None
    credit_card_id: str | None = None


class CreateExpenseSplitRequest(BaseModel):
    account_id: str
    total_amount: str
    currency_code: str = "DOP"
    description: str = Field(..., min_length=1, max_length=500)
    effective_date: str
    notes: str | None = None
    tags: list[str] | None = None
    splits: list[SplitItem]


class SplitItem(BaseModel):
    amount: str
    description: str
    account_id: str | None = None


class ExpenseResponse(BaseModel):
    id: str
    account_id: str
    category_id: str | None = None
    subcategory_id: str | None = None
    transaction_type: str
    status: str
    amount: str
    currency_code: str
    description: str
    notes: str | None = None
    effective_date: str | None = None
    source: str
    tags: list[str] = []
    priority: str = "normal"
    service_id: str | None = None
    subscription_id: str | None = None
    credit_card_id: str | None = None
    created_at: str | None = None


class ListExpensesResponse(BaseModel):
    expenses: list[ExpenseResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ======================================================================
# Templates
# ======================================================================


class CreateTemplateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str
    default_amount: str | None = None
    default_currency: str = "DOP"
    default_account_id: str | None = None
    default_category_id: str | None = None
    default_subcategory_id: str | None = None
    default_notes: str | None = None
    default_frequency: str | None = None
    icon: str | None = None
    color: str | None = None
    sort_order: int = 0


class TemplateResponse(BaseModel):
    id: str
    name: str
    description: str
    default_amount: str | None = None
    default_currency: str
    default_category_id: str | None = None
    default_subcategory_id: str | None = None
    default_notes: str | None = None
    default_frequency: str | None = None
    usage_count: int
    last_used_at: str | None = None
    icon: str | None = None
    color: str | None = None
    created_at: str | None = None


class CreateFromTemplateRequest(BaseModel):
    account_id: str | None = None  # override template default
    amount: str | None = None  # override
    effective_date: str  # required
    notes: str | None = None
    tags: list[str] | None = None


# ======================================================================
# Services
# ======================================================================


class CreateServiceRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    provider: str | None = None
    service_type: str = Field(
        ..., description="electricity, water, gas, internet, phone, cable, other"
    )
    frequency: str = "monthly"
    estimated_amount: str | None = None
    account_number: str | None = None
    billing_day: int | None = None
    due_day: int | None = None
    category_id: str | None = None
    auto_create_expense: bool = False
    icon: str | None = None
    color: str | None = None
    notes: str | None = None


class ServiceResponse(BaseModel):
    id: str
    name: str
    provider: str | None = None
    service_type: str
    frequency: str
    estimated_amount: str | None = None
    account_number: str | None = None
    billing_day: int | None = None
    due_day: int | None = None
    category_id: str | None = None
    last_paid_at: str | None = None
    last_paid_amount: str | None = None
    payment_status: str
    is_active: bool
    auto_create_expense: bool
    icon: str | None = None
    color: str | None = None
    notes: str | None = None
    created_at: str | None = None


class MarkServicePaidRequest(BaseModel):
    amount: str | None = None
    paid_date: str | None = None  # ISO date, defaults to today
    notes: str | None = None


# ======================================================================
# Subscriptions
# ======================================================================


class CreateSubscriptionRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    provider: str | None = None
    amount: str
    currency_code: str = "DOP"
    billing_frequency: str = "monthly"
    account_id: str | None = None
    category_id: str | None = None
    start_date: str  # ISO date
    end_date: str | None = None
    next_billing_date: str | None = None
    website_url: str | None = None
    logo_url: str | None = None
    icon: str | None = None
    color: str | None = None


class SubscriptionResponse(BaseModel):
    id: str
    name: str
    description: str | None = None
    provider: str | None = None
    amount: str
    currency_code: str
    billing_frequency: str
    status: str
    start_date: str
    end_date: str | None = None
    next_billing_date: str | None = None
    cancelled_date: str | None = None
    cancellation_reason: str | None = None
    annual_cost: str | None = None
    auto_detected: bool
    website_url: str | None = None
    logo_url: str | None = None
    created_at: str | None = None


class SubscriptionSummaryResponse(BaseModel):
    active_count: int
    monthly_total: str
    annual_total: str
    cost_per_day: str
    subscriptions: list[dict]
    recommendations: list[str]


# ======================================================================
# Credit Cards
# ======================================================================


class CreateCreditCardRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    account_id: str  # linked financial account
    last_four_digits: str | None = None
    card_network: str | None = None
    credit_limit: str | None = None
    available_credit: str | None = None
    statement_day: int | None = None
    payment_due_day: int | None = None
    interest_rate: str | None = None
    color: str | None = None
    icon: str | None = None


class CreditCardResponse(BaseModel):
    id: str
    name: str
    account_id: str
    last_four_digits: str | None = None
    card_network: str | None = None
    credit_limit: str | None = None
    available_credit: str | None = None
    statement_day: int | None = None
    payment_due_day: int | None = None
    interest_rate: str | None = None
    is_active: bool
    color: str | None = None
    created_at: str | None = None


class CardUtilizationResponse(BaseModel):
    credit_limit: str
    available_credit: str
    used_credit: str
    utilization_percentage: str
    status: str  # healthy, warning, danger


# ======================================================================
# Credit Card Bills
# ======================================================================


class CreateCardBillRequest(BaseModel):
    credit_card_id: str
    statement_date: str  # ISO date
    due_date: str  # ISO date
    total_amount: str
    minimum_payment: str | None = None
    interest_charged: str | None = None
    payment_due_day: int | None = None
    notes: str | None = None


class CardBillResponse(BaseModel):
    id: str
    credit_card_id: str
    statement_date: str
    due_date: str
    total_amount: str
    minimum_payment: str | None = None
    interest_charged: str | None = None
    payment_status: str
    amount_paid: str
    paid_at: str | None = None
    transaction_count: int
    notes: str | None = None
    created_at: str | None = None


# ======================================================================
# Dashboard & Analytics
# ======================================================================


class ExpenseDashboardResponse(BaseModel):
    period_start: str
    period_end: str
    total_expenses: str
    total_count: int
    daily_average: str
    monthly_subscriptions: str
    by_category: list[dict]
    daily_trend: list[dict]


class SpendingPatternsResponse(BaseModel):
    top_categories: list[dict]
    monthly_data: list[dict]
    average_monthly_expense: str
    period: str


class DuplicatesResponse(BaseModel):
    duplicates: list[dict]
    total: int


class RecurringCandidatesResponse(BaseModel):
    candidates: list[dict]
    total: int
