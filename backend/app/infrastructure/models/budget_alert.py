"""Budget Alert model - threshold-based alerts for budgets."""

from __future__ import annotations

import uuid
from datetime import datetime  # noqa: TC003
from decimal import Decimal  # noqa: TC003
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.base import Base

if TYPE_CHECKING:
    from app.infrastructure.models.budget import BudgetModel
    from app.infrastructure.models.user import UserModel


class BudgetAlertModel(Base):
    """Alert triggered when a budget threshold is reached."""

    __tablename__ = "budget_alert"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    budget_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("budget.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # --- Alert Info ---
    alert_type: Mapped[str] = mapped_column(String(30), nullable=False)
    severity: Mapped[str] = mapped_column(String(10), nullable=False, default="warning")
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)

    # --- Threshold Details ---
    threshold_percentage: Mapped[int | None] = mapped_column(Integer, nullable=True)
    current_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=19, scale=4), nullable=True, default=None
    )
    budget_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=19, scale=4), nullable=True, default=None
    )

    # --- Status ---
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_dismissed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # --- Timestamps ---
    triggered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    read_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    dismissed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )

    # --- Relationships ---
    user: Mapped[UserModel] = relationship("UserModel", lazy="noload")
    budget: Mapped[BudgetModel] = relationship("BudgetModel", lazy="selectin")

    def __repr__(self) -> str:
        return (
            f"<BudgetAlertModel(id={self.id}, type={self.alert_type}, "
            f"severity={self.severity}, read={self.is_read})>"
        )
