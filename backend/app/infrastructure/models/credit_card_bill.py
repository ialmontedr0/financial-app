"""Credit Card Bill model - monthly statement tracking."""

from __future__ import annotations

import uuid
from datetime import date, datetime  # noqa: TC003
from decimal import Decimal  # noqa: TC003
from typing import TYPE_CHECKING

from sqlalchemy import (  # noqa: F401
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
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.base import Base

if TYPE_CHECKING:
    from app.infrastructure.models.credit_card import CreditCardModel
    from app.infrastructure.models.user import UserModel


class CreditCardBillModel(Base):
    """Monthly credit card bill/statement."""

    __tablename__ = "credit_card_bill"

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

    # --- Statement Period ---
    statement_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)

    # --- Financial ---
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=19, scale=4), nullable=False, server_default="0"
    )
    minimum_payment: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=19, scale=4), nullable=True, default=None
    )
    interest_charged: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=19, scale=4), nullable=True, default=None
    )

    # --- Payment ---
    payment_status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    amount_paid: Mapped[Decimal] = mapped_column(
        Numeric(precision=19, scale=4), nullable=False, server_default="0"
    )
    paid_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    payment_due_day: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)

    # --- Stats ---
    transaction_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # --- Notes ---
    notes: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)

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
    credit_card: Mapped[CreditCardModel] = relationship("CreditCardModel", lazy="selectin")

    def __repr__(self) -> str:
        return f"<CreditCardBillModel(id={self.id}, statement={self.statement_date}, total={self.total_amount})>"
