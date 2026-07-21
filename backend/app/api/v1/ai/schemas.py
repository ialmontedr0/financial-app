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
