"""Analytics API schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class MonthlyKPIsSchema(BaseModel):
    year: int = Field(None, ge=2000, le=2100)
    month: int = Field(None, ge=1, le=12)


class TrendQuerySchema(BaseModel):
    start_date: str | None = None
    end_date: str | None = None
    period: str = Field("monthly", pattern=r"^(daily|weekly|monthly)$")


class CategoryBreakdownSchema(BaseModel):
    start_date: str | None = None
    end_date: str | None = None
    transaction_type: str = Field("expense", pattern=r"^(income|expense)$")


class HeatmapQuerySchema(BaseModel):
    start_date: str | None = None
    end_date: str | None = None
    granularity: str = Field(
        "day_of_week_month",
        pattern=r"^(day_of_week_month|day_of_week_hour|category_month)$",
    )
