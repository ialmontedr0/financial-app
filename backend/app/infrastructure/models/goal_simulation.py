"""Goal Simulation model - stores what-if scenarios for financial goals."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.base import Base

if TYPE_CHECKING:
    from app.infrastructure.models.financial_goal import FinancialGoalModel


class GoalSimulationModel(Base):
    """What-if simulation for a financial goal."""

    __tablename__ = "goal_simulation"

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

    # Simulation Parameters
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    monthly_contribution: Mapped[Decimal] = mapped_column(
        Numeric(precision=19, scale=4), nullable=False
    )
    lump_sum: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=19, scale=4), nullable=True, default=None
    )
    lump_sum_date: Mapped[date | None] = mapped_column(nullable=True, default=None)
    interest_rate: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=7, scale=4), nullable=True, default=None
    )
    increase_pct: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=5, scale=2), nullable=True, default=None
    )

    # Results
    predicted_completion_date: Mapped[date | None] = mapped_column(nullable=True, default=None)
    predicted_probability: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=5, scale=4), nullable=True, default=None
    )
    total_contributions: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=19, scale=4), nullable=True, default=None
    )
    total_interest: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=19, scale=4), nullable=True, default=None
    )
    months_to_complete: Mapped[int | None] = mapped_column(nullable=True, default=None)

    # Monthly projection
    projection: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)

    # Metadata
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationship
    goal: Mapped[FinancialGoalModel] = relationship("FinancialGoalModel", lazy="noload")

    def __repr__(self) -> str:
        return f"<GoalSimulation(id={self.id}, name={self.name}, monthly={self.monthly_contribution})>"
