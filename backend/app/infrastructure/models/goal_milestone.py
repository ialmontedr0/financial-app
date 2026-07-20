"""Goal Milestone model - tracks progress snapshots for financial goals."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.base import Base

if TYPE_CHECKING:
    from app.infrastructure.models.financial_goal import FinancialGoalModel


class GoalMilestoneModel(Base):
    """Milestone snapshot for a financial goal."""

    __tablename__ = "goal_milestone"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    goal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("financial_goal.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Event
    event_type: Mapped[str] = mapped_column(String(30), nullable=False)

    # Snapshot at event time
    amount_at_event: Mapped[Decimal] = mapped_column(Numeric(precision=19, scale=4), nullable=False)
    target_amount: Mapped[Decimal] = mapped_column(Numeric(precision=19, scale=4), nullable=False)
    pct_complete: Mapped[Decimal] = mapped_column(Numeric(precision=7, scale=4), nullable=False)

    # Contribution detail
    contribution_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=19, scale=4), nullable=True, default=None
    )
    transaction_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("transaction.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
    )

    # Metadata
    notes: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationship
    goal: Mapped[FinancialGoalModel] = relationship("FinancialGoalModel", lazy="noload")

    def __repr__(self) -> str:
        return f"<GoalMilestone(id={self.id}, event={self.event_type}, pct={self.pct_complete})>"
