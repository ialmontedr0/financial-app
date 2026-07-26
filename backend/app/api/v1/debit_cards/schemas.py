"""Pydantic schemas for debit card endpoints."""

from __future__ import annotations

from pydantic import BaseModel, Field


class CreateDebitCardRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    account_id: str
    last_four_digits: str | None = None
    card_network: str | None = None
    is_active: bool = True
    color: str | None = None
    notes: str | None = None


class UpdateDebitCardRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    last_four_digits: str | None = None
    card_network: str | None = None
    is_active: bool | None = None
    color: str | None = None
    notes: str | None = None


class DebitCardResponse(BaseModel):
    id: str
    account_id: str
    name: str
    last_four_digits: str | None = None
    card_network: str | None = None
    is_active: bool
    color: str | None = None
    notes: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class ListDebitCardsResponse(BaseModel):
    debit_cards: list[DebitCardResponse]
    total: int
