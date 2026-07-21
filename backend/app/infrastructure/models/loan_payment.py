"""Loan payment database model."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Index, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.base import Base

if TYPE_CHECKING:
    from app.infrastructure.models.loan import LoanModel


class LoanPaymentModel(Base):
    __tablename__ = "loan_payment"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    loan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("loan.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    amount: Mapped[Decimal] = mapped_column(Numeric(precision=19, scale=4), nullable=False)
    principal_portion: Mapped[Decimal] = mapped_column(
        Numeric(precision=19, scale=4), nullable=False
    )
    interest_portion: Mapped[Decimal] = mapped_column(
        Numeric(precision=19, scale=4), nullable=False
    )
    penalty_portion: Mapped[Decimal] = mapped_column(
        Numeric(precision=19, scale=4), nullable=False, default=0
    )

    payment_date: Mapped[date] = mapped_column(Date, nullable=False)
    payment_method: Mapped[str] = mapped_column(
        Enum(
            "bank_transfer",
            "cash",
            "auto_debit",
            "check",
            "online",
            "mobile",
            name="loan_payment_method_enum",
            create_type=False,
        ),
        nullable=False,
        default="bank_transfer",
    )
    reference_number: Mapped[str | None] = mapped_column(String(100), nullable=True, default=None)
    status: Mapped[str] = mapped_column(
        Enum(
            "pending",
            "completed",
            "failed",
            "reversed",
            name="loan_payment_status_enum",
            create_type=False,
        ),
        nullable=False,
        default="completed",
    )

    balance_after: Mapped[Decimal] = mapped_column(Numeric(precision=19, scale=4), nullable=False)
    is_extra_payment: Mapped[bool] = mapped_column(nullable=False, default=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # relationships
    loan: Mapped[LoanModel] = relationship(back_populates="payments", lazy="noload")  # type: ignore[name-defined]

    __table_args__ = (Index("ix_loan_payment_date", "loan_id", "payment_date"),)

    def __repr__(self) -> str:
        return f"<LoanPayment {self.amount} | {self.payment_date} | {self.status}>"
