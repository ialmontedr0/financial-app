"""AI Model Registry - tracks model versions, metrics, and lifecycle."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.base import Base

if TYPE_CHECKING:
    from app.infrastructure.models.user import UserModel


class AIModelRegistryModel(Base):
    """Tracks every trained model version with metrics and lifecycle."""

    __tablename__ = "ai_model_registry"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    model_type: Mapped[str] = mapped_column(String(50), nullable=False)
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(200), nullable=True)

    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    is_production: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    accuracy: Mapped[Decimal | None] = mapped_column(Numeric(precision=7, scale=4), nullable=True)
    precision_score: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=7, scale=4), nullable=True
    )
    recall_score: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=7, scale=4), nullable=True
    )
    f1_score: Mapped[Decimal | None] = mapped_column(Numeric(precision=7, scale=4), nullable=True)
    mse: Mapped[Decimal | None] = mapped_column(Numeric(precision=15, scale=6), nullable=True)
    mae: Mapped[Decimal | None] = mapped_column(Numeric(precision=15, scale=6), nullable=True)
    auc_roc: Mapped[Decimal | None] = mapped_column(Numeric(precision=7, scale=4), nullable=True)

    training_samples: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    training_duration_seconds: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=10, scale=2), nullable=True
    )
    training_started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    training_completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    hyperparameters: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    feature_names: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    model_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user: Mapped[UserModel] = relationship("UserModel", lazy="noload")

    def __repr__(self) -> str:
        return (
            f"<AIModelRegistryModel(id={self.id}, type={self.model_type}, "
            f"version={self.version}, status={self.status}, "
            f"is_production={self.is_production})>"
        )
