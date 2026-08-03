"""Tax API schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class CreateTaxCategorySchema(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    tax_year: int = Field(..., ge=1900, le=2200)
    description: str | None = None


class CreateTaxDeductionSchema(BaseModel):
    description: str = Field(..., min_length=1, max_length=500)
    amount: float = Field(..., gt=0)
    date: str = Field(..., description="ISO date, e.g. 2026-03-15")
    tax_year: int = Field(..., ge=1900, le=2200)
    category_id: str | None = None
    deductible: float | None = Field(None, ge=0)
    receipt_url: str | None = None


class UpdateTaxDeductionSchema(BaseModel):
    description: str | None = Field(None, min_length=1, max_length=500)
    amount: float | None = Field(None, gt=0)
    date: str | None = None
    tax_year: int | None = Field(None, ge=1900, le=2200)
    category_id: str | None = None
    deductible: float | None = Field(None, ge=0)
    receipt_url: str | None = None
