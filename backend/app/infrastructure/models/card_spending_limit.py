"""Card Spending Limit model - custom limits per credit card."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.base import Base

if TYPE_CHECKING:
    from app.infrastructure.models.credit_card import CreditCardModel
    from app.infrastructure.models.user import UserModel


class CardSpendingLimitModel(Base):
    """A spending limit attached to a credit card."""

    __tablename__ = "card_spending_limit"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    credit_card_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("credit_card.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    limit_type: Mapped[str] = mapped_column(String(20), nullable=False)
    limit_amount: Mapped[Decimal] = mapped_column(Numeric(precision=19, scale=4), nullable=False)
    spent_amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=19, scale=4), nullable=False, server_default="0"
    )

    category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("category.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
    )

    period_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)
    period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)

    alert_threshold: Mapped[int] = mapped_column(nullable=False, default=80)
    alert_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    description: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )

    user: Mapped[UserModel] = relationship("UserModel", lazy="noload")
    credit_card: Mapped[CreditCardModel] = relationship("CreditCardModel", lazy="selectin")

    def __repr__(self) -> str:
        return f"<CardSpendingLimit(id={self.id}, type={self.limit_type}, limit={self.limit_amount})>"
