"""OCR API schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class OcrSuggestionSchema(BaseModel):
    amount: float | None = Field(None, ge=0)
    date: str | None = Field(None, description="ISO date, e.g. 2026-01-01")
    merchant: str | None = None
    currency: str | None = None
    type: str = Field("expense", pattern=r"^(expense|income)$")


class OcrDataSchema(BaseModel):
    text: str | None = None
    amount: float | None = None
    amount_decimal: str | None = None
    date: str | None = None
    merchant: str | None = None
    currency: str | None = None
    confidence: str = Field("low", pattern=r"^(low|medium|high)$")


class OcrExtractResponseSchema(BaseModel):
    success: bool
    data: OcrDataSchema
    suggestions: OcrSuggestionSchema
    warnings: list[str] = []


class OcrStatusSchema(BaseModel):
    enabled: bool
    tesseract_available: bool
    supported_extensions: list[str]
