"""Investments API schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class CreateAssetSchema(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    asset_type: str = Field(
        "stock",
        pattern=r"^(stock|bond|etf|crypto|mutual_fund|real_estate|commodity)$",
    )
    currency: str = Field("USD", max_length=3)
    symbol: str | None = Field(None, max_length=20)
    current_price: float | None = Field(None, ge=0)


class UpdateAssetPriceSchema(BaseModel):
    current_price: float = Field(..., ge=0)


class CreatePortfolioSchema(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None


class CreateInvestmentTransactionSchema(BaseModel):
    type: str = Field(..., pattern=r"^(buy|sell|dividend|fee)$")
    quantity: float = Field(..., gt=0)
    price_per_unit: float = Field(..., ge=0)
    fees: float = Field(0, ge=0)
    portfolio_id: str | None = None
    date: str | None = Field(None, description="ISO date, e.g. 2026-08-03")
    total_amount: float | None = Field(None, ge=0)
    notes: str | None = None


class AddPricePointSchema(BaseModel):
    close_price: float = Field(..., ge=0)
    date: str | None = Field(None, description="ISO date, e.g. 2026-08-03")
    open_price: float | None = Field(None, ge=0)
    high_price: float | None = Field(None, ge=0)
    low_price: float | None = Field(None, ge=0)
    volume: float | None = Field(None, ge=0)
