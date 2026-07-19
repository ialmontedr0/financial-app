"""Pydantic schemas for Wallets API."""

from __future__ import annotations

from pydantic import BaseModel, Field


# ============================================================
# Create Wallet
# ============================================================
class CreateWalletRequest(BaseModel):
    """Request to create a new wallet."""

    name: str = Field(..., min_length=1, max_length=100, description="Wallet name")
    description: str | None = Field(None, max_length=500, description="Wallet description")
    wallet_type: str = Field(
        default="personal",
        description="personal, business, savings, investment, daily, emergency",
    )
    icon: str | None = Field(None, max_length=500, description="Icon URL or emoji")
    color: str | None = Field(None, max_length=7, description="Hex color (#RRGGBB)")
    sort_order: int = Field(default=0, description="Display order")


class WalletResponse(BaseModel):
    """Wallet response."""

    id: str
    name: str
    description: str | None = None
    wallet_type: str
    status: str = "active"
    icon: str | None = None
    color: str | None = None
    sort_order: int = 0
    created_at: str | None = None
    updated_at: str | None = None


# ============================================================
# Update Wallet
# ============================================================
class UpdateWalletRequest(BaseModel):
    """Request to update a wallet (all fields optional)."""

    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)
    wallet_type: str | None = None
    icon: str | None = Field(None, max_length=500)
    color: str | None = Field(None, max_length=7)
    sort_order: int | None = None
    status: str | None = Field(None, description="active, archived")


# ============================================================
# Delete Wallet
# ============================================================
class DeleteWalletResponse(BaseModel):
    """Wallet deletion response."""

    message: str
    wallet_id: str


# ============================================================
# List Wallets
# ============================================================
class WalletListItem(BaseModel):
    """Wallet list item (slim)."""

    id: str
    name: str
    description: str | None = None
    wallet_type: str
    status: str
    icon: str | None = None
    color: str | None = None
    sort_order: int = 0
    account_count: int = 0
    created_at: str | None = None


class ListWalletsResponse(BaseModel):
    """List of wallets."""

    wallets: list[WalletListItem]
    total: int


# ============================================================
# Wallet Detail (with accounts)
# ============================================================
class WalletAccountItem(BaseModel):
    """Account within a wallet."""

    id: str
    name: str
    account_type: str
    currency_code: str
    balance: str
    status: str


class WalletDetailResponse(BaseModel):
    """Wallet with linked accounts."""

    id: str
    name: str
    description: str | None = None
    wallet_type: str
    status: str = "active"
    icon: str | None = None
    color: str | None = None
    sort_order: int = 0
    accounts: list[WalletAccountItem] = []
    created_at: str | None = None
    updated_at: str | None = None


# ============================================================
# Add/Remove Account
# ============================================================
class AddAccountRequest(BaseModel):
    """Request to add an account to a wallet."""

    account_id: str = Field(..., description="Financial account UUID")
    notes: str | None = Field(None, max_length=500, description="Optional notes")


class AddAccountResponse(BaseModel):
    """Account added response."""

    message: str
    wallet_id: str
    account_id: str
    added_at: str | None = None


class RemoveAccountResponse(BaseModel):
    """Account removed response."""

    message: str
    wallet_id: str
    account_id: str


# ============================================================
# Balance
# ============================================================
class CurrencyBalance(BaseModel):
    """Balance per currency."""

    currency: str
    account_count: int
    total_balance: str


class WalletBalanceResponse(BaseModel):
    """Computed wallet balance."""

    wallet_id: str
    wallet_name: str
    total_accounts: int
    by_currency: dict[str, CurrencyBalance]


# ============================================================
# Liquidity
# ============================================================
class LiquidityItem(BaseModel):
    """Liquidity breakdown per account type."""

    account_type: str
    account_count: int
    total_balance: str
    liquidity_level: str


class WalletLiquidityResponse(BaseModel):
    """Wallet liquidity analysis."""

    wallet_id: str
    wallet_name: str
    overall_level: str
    breakdown: dict[str, LiquidityItem]
    total_accounts: int
