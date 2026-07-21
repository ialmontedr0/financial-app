"""Loan amortization entry database model."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, Index, Integer, Numeric, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.base import Base

if TYPE_CHECKING:
    from app.infrastructure.models.loan import LoanModel


class LoanAmortizationEntryModel(Base):
    __tablename__ = "loan_amortization_entry"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    loan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("loan.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    entry_number: Mapped[int] = mapped_column(Integer, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    payment_amount: Mapped[Decimal] = mapped_column(Numeric(precision=19, scale=4), nullable=False)
    principal_portion: Mapped[Decimal] = mapped_column(
        Numeric(precision=19, scale=4), nullable=False
    )
    interest_portion: Mapped[Decimal] = mapped_column(
        Numeric(precision=19, scale=4), nullable=False
    )
    balance_after: Mapped[Decimal] = mapped_column(Numeric(precision=19, scale=4), nullable=False)
    total_interest_to_date: Mapped[Decimal] = mapped_column(
        Numeric(precision=19, scale=4), nullable=False, default=0
    )
    total_principal_to_date: Mapped[Decimal] = mapped_column(
        Numeric(precision=19, scale=4), nullable=False, default=0
    )
    is_paid: Mapped[bool] = mapped_column(nullable=False, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # relationships
    loan: Mapped[LoanModel] = relationship(back_populates="amortization_entries", lazy="noload")  # type: ignore[name-defined]

    __table_args__ = (Index("ix_amortization_loan_number", "loan_id", "entry_number", unique=True),)

    def __repr__(self) -> str:
        return f"<AmortizationEntry #{self.entry_number} | {self.due_date} | balance={self.balance_after}>"
