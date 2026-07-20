"""Credit Card model - lightweight card tracking for expense context."""

from __future__ import annotations

import uuid
from datetime import date, datetime  # noqa: F401, TC003
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
    from app.infrastructure.models.financial_account import FinancialAccountModel
    from app.infrastructure.models.user import UserModel


class CreditCardModel(Base):
    """Credit card - links to a financial account for expense tracking."""

    __tablename__ = "credit_card"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("financial_account.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # --- Card Identity ---
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_four_digits: Mapped[str | None] = mapped_column(String(4), nullable=True, default=None)
    card_network: Mapped[str | None] = mapped_column(
        String(20), nullable=True, default=None
    )  # visa, mastercard, amex

    # --- Limits ---
    credit_limit: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=19, scale=4), nullable=True, default=None
    )
    available_credit: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=19, scale=4), nullable=True, default=None
    )

    # --- Dates ---
    statement_day: Mapped[int | None] = mapped_column(
        Integer, nullable=True, default=None
    )  # day of month (1-28)
    payment_due_day: Mapped[int | None] = mapped_column(
        Integer, nullable=True, default=None
    )  # day of month

    # --- Interest ---
    interest_rate: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=5, scale=4), nullable=True, default=None
    )  # annual rate

    # --- Settings ---
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    include_in_totals: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # --- Display ---
    color: Mapped[str | None] = mapped_column(String(7), nullable=True, default=None)
    icon: Mapped[str | None] = mapped_column(String(500), nullable=True, default=None)

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
    account: Mapped[FinancialAccountModel] = relationship("FinancialAccountModel", lazy="selectin")

    def __repr__(self) -> str:
        return f"<CreditCardModel(id={self.id}, name={self.name}, last4={self.last_four_digits})>"
