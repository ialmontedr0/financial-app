"""Financial Goal model - intelligent goal tracking and prediction."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.base import Base

if TYPE_CHECKING:
    from app.infrastructure.models.category import CategoryModel
    from app.infrastructure.models.financial_account import FinancialAccountModel
    from app.infrastructure.models.user import UserModel


class FinancialGoalModel(Base):
    """Financial goal for tracking savings, debt payoff, investments, etc."""

    __tablename__ = "financial_goal"
    __table_args__ = (
        Index("ix_financial_goal_user_status", "user_id", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Identity
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)

    # Goal Type
    goal_type: Mapped[str] = mapped_column(String(30), nullable=False, default="savings")

    # Financials
    target_amount: Mapped[Decimal] = mapped_column(Numeric(precision=19, scale=4), nullable=False)
    current_amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=19, scale=4), nullable=False, server_default="0"
    )

    # Timeline
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    target_date: Mapped[date] = mapped_column(Date, nullable=False)
    completed_date: Mapped[date | None] = mapped_column(Date, nullable=True, default=None)

    # Status & Priority
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # Monthly Contribution
    monthly_contribution: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=19, scale=4), nullable=True, default=None
    )
    auto_contribute: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Interest / Growth
    interest_rate: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=7, scale=4), nullable=True, default=None
    )
    compound_frequency: Mapped[str | None] = mapped_column(String(20), nullable=True, default=None)

    # Links
    account_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("financial_account.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
    )
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("category.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
    )

    # AI Prediction Cache
    predicted_completion_date: Mapped[date | None] = mapped_column(
        Date, nullable=True, default=None
    )
    predicted_probability: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=5, scale=4), nullable=True, default=None
    )
    recommended_monthly: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=19, scale=4), nullable=True, default=None
    )
    prediction_updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )

    # Milestones
    milestone_reached_pct: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    adjustment_history: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)

    # Display
    icon: Mapped[str | None] = mapped_column(String(500), nullable=True, default=None)
    color: Mapped[str | None] = mapped_column(String(7), nullable=True, default=None)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True, default=None)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )

    # Relationships
    user: Mapped[UserModel] = relationship("UserModel", lazy="noload")
    account: Mapped[FinancialAccountModel | None] = relationship(
        "FinancialAccountModel", lazy="selectin"
    )
    category: Mapped[CategoryModel | None] = relationship("CategoryModel", lazy="selectin")

    def __repr__(self) -> str:
        return f"<FinancialGoal(id={self.id}, name={self.name}, target={self.target_amount}, current={self.current_amount})>"
