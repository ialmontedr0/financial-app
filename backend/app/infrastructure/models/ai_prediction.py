from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.base import Base

if TYPE_CHECKING:
    from app.infrastructure.models.user import UserModel


class AIPredictionModel(Base):
    """Almacena cada salida deprediccion de IA para auditar y explicar."""

    __tablename__ = "ai_prediction"
    __table_args__ = (
        Index("ix_ai_prediction_user_type", "user_id", "prediction_type"),
        Index("ix_ai_prediction_user_created", "user_id", "created_at"),
        Index("ix_ai_prediction_model_version", "model_version"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    prediction_type: Mapped[str] = mapped_column(String(30), nullable=False)
    model_version: Mapped[str] = mapped_column(String(50), nullable=False)
    confidence: Mapped[Decimal | None] = mapped_column(Numeric(precision=5, scale=4), nullable=True)

    predicted_value: Mapped[str | None] = mapped_column(String(200), nullable=True)
    predicted_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=19, scale=4), nullable=True
    )
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    features_used: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    transaction_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("transaction.id", ondelete="SET NULL"),
        nullable=True,
    )

    was_correct: Mapped[bool | None] = mapped_column(nullable=True, default=None)
    feedback_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped[UserModel] = relationship("UserModel", lazy="noload")

    def __repr__(self) -> str:
        return (
            f"<AIPredictionModel(id={self.id}, type={self.prediction_type}, "
            f"model={self.model_version}, confidence={self.confidence})>"
        )
