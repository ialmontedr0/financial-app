"""Subscription model - subscription lifecycle tracking."""

from __future__ import annotations

import uuid
from datetime import date, datetime  # noqa: TC003
from decimal import Decimal  # noqa: TC003
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.base import Base

if TYPE_CHECKING:
    from app.infrastructure.models.category import CategoryModel
    from app.infrastructure.models.financial_account import FinancialAccountModel
    from app.infrastructure.models.user import UserModel


class SubscriptionModel(Base):
    """Subscription tracking for recurring digital services."""

    __tablename__ = "subscription"

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
    provider: Mapped[str | None] = mapped_column(
        String(200), nullable=True, default=None
    )  # Netflix, Spotify, etc.

    # --- Financial ---
    amount: Mapped[Decimal] = mapped_column(Numeric(precision=19, scale=4), nullable=False)
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False, default="DOP")
    billing_frequency: Mapped[str] = mapped_column(
        String(20), nullable=False, default="monthly"
    )  # monthly, yearly, etc.

    # --- Account ---
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

    # --- Lifecycle ---
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True, default=None)
    next_billing_date: Mapped[date | None] = mapped_column(Date, nullable=True, default=None)
    cancelled_date: Mapped[date | None] = mapped_column(Date, nullable=True, default=None)
    cancellation_reason: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)

    # --- Tracking ---
    linked_recurring_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("transaction_recurring.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
    )
    auto_detected: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # --- Annual Cost ---
    annual_cost: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=19, scale=4), nullable=True, default=None
    )
    annual_cost_calculated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )

    # --- Display ---
    icon: Mapped[str | None] = mapped_column(String(500), nullable=True, default=None)
    color: Mapped[str | None] = mapped_column(String(7), nullable=True, default=None)
    website_url: Mapped[str | None] = mapped_column(String(500), nullable=True, default=None)
    logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True, default=None)

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
    account: Mapped[FinancialAccountModel | None] = relationship(
        "FinancialAccountModel", lazy="selectin"
    )
    category: Mapped[CategoryModel | None] = relationship("CategoryModel", lazy="selectin")

    def __repr__(self) -> str:
        return f"<SubscriptionModel(id={self.id}, name={self.name}, status={self.status}, amount={self.amount})>"
