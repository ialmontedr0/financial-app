"""Pydantic schemas for search endpoints."""

from pydantic import BaseModel


class Suggestion(BaseModel):
    type: str
    id: str
    label: str


class SuggestionResponse(BaseModel):
    suggestions: list[Suggestion]


class SearchResult(BaseModel):
    id: str
    description: str
    amount: str
    transaction_type: str
    effective_date: str | None
    category_name: str | None = None
    account_name: str | None = None


class SearchResponse(BaseModel):
    results: list[SearchResult]
    total: int
