"""AI API schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ClassifyRequestSchema(BaseModel):
    transaction_id: str
    description: str = Field(..., min_length=1, max_length=500)
    category_id: str | None = None


class TrainPredictorRequestSchema(BaseModel):
    target_type: str = Field("expense", pattern=r"^(expense|income)$")


class AnomalyDetectRequestSchema(BaseModel):
    engine: str = Field("isolation_forest", pattern=r"^(isolation_forest|autoencoder)$")


class HabitAnalysisResponse(BaseModel):
    habits: dict
    overall_habit_score: int = Field(..., ge=0, le=100)
    total_recommendations: int


class HabitTrendsResponse(BaseModel):
    trends: dict
    months_analyzed: int


class RiskAssessmentResponse(BaseModel):
    financial_health_score: int = Field(..., ge=0, le=100)
    risk_factors: list[dict]
    metrics: dict
    recommendations: list[dict]


class HealthScoreResponse(BaseModel):
    financial_health_score: int = Field(..., ge=0, le=100)
    risk_count: int
    top_risk: dict | None


class SavingsOptimizeResponse(BaseModel):
    allocation_50_30_20: dict
    goal_allocation: dict
    debt_strategy: dict
    seasonal_opportunities: dict
    estimated_total_savings: float
    recommendations: list[dict]


class SavingsSimulateResponse(BaseModel):
    monthly_amount: float
    months: int
    annual_return_pct: float
    final_balance: float
    total_contributed: float
    total_interest: float
    projections: list[dict]


class ExplanationResponse(BaseModel):
    headline: str
    why: str
    how: str
    impact: str
    action: str
    tone: str
    personalized: bool
    rec_type: str
    priority: str
    estimated_savings: float
    confidence: float


class DashboardResponse(BaseModel):
    habits: dict
    risks: dict
    savings: dict
    recommendations: dict
