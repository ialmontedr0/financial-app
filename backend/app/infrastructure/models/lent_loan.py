"""Lent loan (préstamo otorgado) ORM models.

A "lent loan" is money the user lends to a third party at a fixed term with
a fixed installment (cuota). It behaves like an investment: the user receives
periodic payments (principal + interest) until the balance is paid off.

Entities:
  * LentLoanModel        — the loan given out (receivable asset).
  * LentLoanPaymentModel — payments the user receives from the borrower.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.base import Base

if TYPE_CHECKING:  # pragma: no cover
    from app.infrastructure.models.financial_account import FinancialAccountModel
    from app.infrastructure.models.user import UserModel


class LentLoanModel(Base):
    __tablename__ = "lent_loan"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    account_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("financial_account.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
    )

    borrower_name: Mapped[str] = mapped_column(String(200), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)

    # Money out
    principal_amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=19, scale=4), nullable=False
    )
    annual_interest_rate: Mapped[Decimal] = mapped_column(
        Numeric(precision=8, scale=4), nullable=False
    )
    term_months: Mapped[int] = mapped_column(nullable=False)
    payment_frequency: Mapped[str] = mapped_column(
        Enum("monthly", "bi_weekly", "weekly", name="lent_loan_frequency_enum", create_type=False),
        nullable=False,
        default="monthly",
    )
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False, default="DOP")

    # Money received back
    monthly_payment: Mapped[Decimal] = mapped_column(
        Numeric(precision=19, scale=4), nullable=False
    )
    current_balance: Mapped[Decimal] = mapped_column(
        Numeric(precision=19, scale=4), nullable=False
    )
    total_received: Mapped[Decimal] = mapped_column(
        Numeric(precision=19, scale=4), nullable=False, default=0
    )
    total_interest_expected: Mapped[Decimal] = mapped_column(
        Numeric(precision=19, scale=4), nullable=False, default=0
    )
    total_interest_received: Mapped[Decimal] = mapped_column(
        Numeric(precision=19, scale=4), nullable=False, default=0
    )

    # Dates
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True, default=None)
    first_payment_date: Mapped[date | None] = mapped_column(Date, nullable=True, default=None)
    next_payment_date: Mapped[date | None] = mapped_column(Date, nullable=True, default=None)
    final_payment_date: Mapped[date | None] = mapped_column(Date, nullable=True, default=None)
    paid_off_date: Mapped[date | None] = mapped_column(Date, nullable=True, default=None)

    status: Mapped[str] = mapped_column(
        Enum(
            "active",
            "paid_off",
            "defaulted",
            "cancelled",
            name="lent_loan_status_enum",
            create_type=False,
        ),
        nullable=False,
        default="active",
    )
    is_collateralized: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # relationships
    user: Mapped[UserModel] = relationship("UserModel", lazy="noload")  # type: ignore[name-defined]
    account: Mapped["FinancialAccountModel | None"] = relationship("FinancialAccountModel", lazy="noload")
    payments: Mapped[list["LentLoanPaymentModel"]] = relationship(  # type: ignore[name-defined]
        back_populates="lent_loan", lazy="selectin", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_lent_loan_user_status", "user_id", "status"),
        Index("ix_lent_loan_user_term", "user_id", "term_months"),
    )

    def __repr__(self) -> str:
        return f"<LentLoan {self.borrower_name} | {self.currency_code} | balance={self.current_balance}>"


class LentLoanPaymentModel(Base):
    __tablename__ = "lent_loan_payment"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lent_loan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("lent_loan.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    amount: Mapped[Decimal] = mapped_column(Numeric(precision=19, scale=4), nullable=False)
    principal_portion: Mapped[Decimal] = mapped_column(
        Numeric(precision=19, scale=4), nullable=False, default=0
    )
    interest_portion: Mapped[Decimal] = mapped_column(
        Numeric(precision=19, scale=4), nullable=False, default=0
    )
    received_date: Mapped[date] = mapped_column(Date, nullable=False)
    payment_method: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="bank_transfer",
    )
    reference_number: Mapped[str | None] = mapped_column(String(100), nullable=True, default=None)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # relationships
    user: Mapped[UserModel] = relationship("UserModel", lazy="noload")  # type: ignore[name-defined]
    lent_loan: Mapped[LentLoanModel] = relationship(  # type: ignore[name-defined]
        back_populates="payments", lazy="noload"
    )

    __table_args__ = (Index("ix_lent_loan_payment_loan", "lent_loan_id"),)

    def __repr__(self) -> str:
        return f"<LentLoanPayment {self.amount} on {self.received_date}>"