"""Card Alert model - alerts for credit card events."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.base import Base

if TYPE_CHECKING:
    from app.infrastructure.models.credit_card import CreditCardModel
    from app.infrastructure.models.user import UserModel


class CardAlertModel(Base):
    """Alert triggered by credit card events."""

    __tablename__ = "card_alert"

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

    alert_type: Mapped[str] = mapped_column(String(30), nullable=False)
    severity: Mapped[str] = mapped_column(String(10), nullable=False, default="warning")
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)

    threshold_percentage: Mapped[int | None] = mapped_column(Integer, nullable=True)
    current_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=19, scale=4), nullable=True, default=None
    )
    limit_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=19, scale=4), nullable=True, default=None
    )

    credit_card_bill_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("credit_card_bill.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
    )

    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_dismissed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    triggered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    read_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    dismissed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )

    user: Mapped[UserModel] = relationship("UserModel", lazy="noload")
    credit_card: Mapped[CreditCardModel] = relationship("CreditCardModel", lazy="selectin")

    def __repr__(self) -> str:
        return f"<CardAlert(id={self.id}, type={self.alert_type}, severity={self.severity})>"
