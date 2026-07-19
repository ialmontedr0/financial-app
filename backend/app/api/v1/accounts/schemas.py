"""Pydantic schemas for Accounts API."""

from __future__ import annotations

from pydantic import BaseModel, Field


# ============================================================
# Create Account
# ============================================================
class CreateAccountRequest(BaseModel):
    """Request to create a new financial account."""

    name: str = Field(..., min_length=1, max_length=100, description="Account name")
    account_type: str = Field(
        ...,
        description="bank, cash, savings, checking, wallet, crypto",
    )
    currency_code: str = Field(
        default="DOP",
        max_length=3,
        description="ISO 4217 currency code",
    )
    initial_balance: float = Field(
        default=0.0,
        description="Opening balance",
    )
    institution: str | None = Field(
        None,
        max_length=200,
        description="Bank or provider name",
    )
    account_number_last4: str | None = Field(
        None,
        max_length=4,
        description="Last 4 digits of account number",
    )
    icon: str | None = Field(None, max_length=500, description="Icon URL or emoji")
    color: str | None = Field(
        None,
        max_length=7,
        description="Hex color for UI (#RRGGBB)",
    )
    notes: str | None = Field(None, max_length=1000, description="Free text notes")
    include_in_net_worth: bool = Field(default=True, description="Include in net worth calc")
    include_in_totals: bool = Field(default=True, description="Include in totals")
    sort_order: int = Field(default=0, description="Display order")


class AccountResponse(BaseModel):
    """Financial account response."""

    id: str
    name: str
    account_type: str
    status: str = "active"
    currency_code: str
    balance: str
    initial_balance: str | None = None
    institution: str | None = None
    account_number_last4: str | None = None
    icon: str | None = None
    color: str | None = None
    notes: str | None = None
    include_in_net_worth: bool = True
    include_in_totals: bool = True
    sort_order: int = 0
    created_at: str | None = None
    updated_at: str | None = None


# ============================================================
# Update Account
# ============================================================
class UpdateAccountRequest(BaseModel):
    """Request to update a financial account (all fields optional)."""

    name: str | None = Field(None, min_length=1, max_length=100)
    institution: str | None = Field(None, max_length=200)
    account_number_last4: str | None = Field(None, max_length=4)
    icon: str | None = Field(None, max_length=500)
    color: str | None = Field(None, max_length=7)
    notes: str | None = Field(None, max_length=1000)
    include_in_net_worth: bool | None = None
    include_in_totals: bool | None = None
    sort_order: int | None = None
    status: str | None = Field(None, description="active, inactive, archived, frozen")


class UpdateAccountResponse(BaseModel):
    """Updated account response."""

    message: str = "Account updated successfully"


# ============================================================
# Delete Account
# ============================================================
class DeleteAccountResponse(BaseModel):
    """Account deletion response."""

    message: str
    account_id: str


# ============================================================
# List Accounts
# ============================================================
class AccountListItem(BaseModel):
    """Account list item (slim)."""

    id: str
    name: str
    account_type: str
    status: str
    currency_code: str
    balance: str
    institution: str | None = None
    icon: str | None = None
    color: str | None = None
    include_in_net_worth: bool = True
    sort_order: int = 0
    created_at: str | None = None


class ListAccountsResponse(BaseModel):
    """List of financial accounts."""

    accounts: list[AccountListItem]
    total: int


# ============================================================
# Account Summary
# ============================================================
class CurrencySummary(BaseModel):
    """Summary per currency."""

    currency: str
    account_count: int
    total_balance: str


class AccountSummaryResponse(BaseModel):
    """Aggregated account summary."""

    total_accounts: int
    by_currency: dict[str, CurrencySummary]
