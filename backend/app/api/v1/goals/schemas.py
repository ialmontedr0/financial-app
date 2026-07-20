"""Pydantic schemas for financial goals endpoints."""

from __future__ import annotations

from pydantic import BaseModel, Field


class CreateGoalRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    target_amount: str = Field(...)
    goal_type: str = Field("savings")
    start_date: str | None = None
    target_date: str | None = None
    monthly_contribution: str | None = None
    interest_rate: str | None = None
    compound_frequency: str | None = None
    account_id: str | None = None
    category_id: str | None = None
    priority: int = Field(1, ge=1, le=5)
    auto_contribute: bool = False
    icon: str | None = None
    color: str | None = None
    image_url: str | None = None


class GoalResponse(BaseModel):
    id: str
    name: str
    goal_type: str
    target_amount: str
    current_amount: str
    status: str
    priority: int


class GoalSummaryResponse(BaseModel):
    total_goals: int
    active_goals: int
    completed_goals: int
    total_target_amount: str
    total_current_amount: str
    overall_progress_pct: float
    behind_schedule_count: int
    on_track_count: int


class CreateSimulationRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    monthly_contribution: str = Field(...)
    lump_sum: str | None = None
    lump_sum_date: str | None = None
    interest_rate: str | None = None
    increase_pct: str | None = None
    notes: str | None = None
