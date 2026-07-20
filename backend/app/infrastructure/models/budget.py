"""Budget model - intelligent budget tracking and management."""

from __future__ import annotations

import uuid
from datetime import date, datetime  # noqa: TC003
from decimal import Decimal  # noqa: TC003
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
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


class BudgetModel(Base):
    """Budget for tracking spending limits.

    Supports multiple budget types:
    - total: Overall spending limit for the period
    - category: Limit per category
    - account: Limit per account
    """

    __tablename__ = "budget"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # --- Identity ---
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)

    # --- Budget Type ---
    budget_type: Mapped[str] = mapped_column(String(20), nullable=False)

    # --- Amounts ---
    amount: Mapped[Decimal] = mapped_column(Numeric(precision=19, scale=4), nullable=False)
    spent: Mapped[Decimal] = mapped_column(
        Numeric(precision=19, scale=4), nullable=False, server_default="0"
    )
    remaining: Mapped[Decimal] = mapped_column(
        Numeric(precision=19, scale=4), nullable=False, server_default="0"
    )

    # --- Period ---
    period: Mapped[str] = mapped_column(String(20), nullable=False, default="monthly")
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)

    # --- Links ---
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("category.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
    )
    account_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("financial_account.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
    )

    # --- Alerts ---
    alert_threshold: Mapped[int] = mapped_column(Integer, nullable=False, default=80)
    alert_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # --- Auto-adjustment ---
    auto_adjust: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    adjustment_history: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)

    # --- Rollover ---
    rollover: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    rollover_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=19, scale=4), nullable=True, default=None
    )

    # --- Strategy ---
    strategy: Mapped[str | None] = mapped_column(String(30), nullable=True, default=None)

    # --- Status ---
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # --- Display ---
    icon: Mapped[str | None] = mapped_column(String(500), nullable=True, default=None)
    color: Mapped[str | None] = mapped_column(String(7), nullable=True, default=None)

    # --- Timestamps ---
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )

    # --- Relationships ---
    user: Mapped[UserModel] = relationship("UserModel", lazy="noload")
    category: Mapped[CategoryModel | None] = relationship("CategoryModel", lazy="selectin")
    account: Mapped[FinancialAccountModel | None] = relationship(
        "FinancialAccountModel", lazy="selectin"
    )

    def __repr__(self) -> str:
        return (
            f"<BudgetModel(id={self.id}, name={self.name}, type={self.budget_type}, "
            f"amount={self.amount}, spent={self.spent})>"
        )
