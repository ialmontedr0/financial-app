from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.base import Base

if TYPE_CHECKING:
    from app.infrastructure.models.loan_amortization_entry import LoanAmortizationEntryModel
    from app.infrastructure.models.loan_payment import LoanPaymentModel
    from app.infrastructure.models.user import UserModel


class LoanModel(Base):
    __tablename__ = "loan"

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

    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True, default=None)
    loan_type: Mapped[str] = mapped_column(
        Enum(
            "personal",
            "mortgage",
            "auto",
            "student",
            "business",
            "personal_line",
            "payday",
            "microloan",
            "consolidation",
            name="loan_type_enum",
            create_type=False,
        ),
        nullable=False,
        default="personal",
    )
    lender_name: Mapped[str | None] = mapped_column(String(200), nullable=True, default=None)
    account_number: Mapped[str | None] = mapped_column(String(100), nullable=True, default=None)

    principal_amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=19, scale=4), nullable=False
    )
    current_balance: Mapped[Decimal] = mapped_column(
        Numeric(precision=19, scale=4), nullable=False
    )
    annual_interest_rate: Mapped[Decimal] = mapped_column(
        Numeric(precision=8, scale=4), nullable=False
    )
    interest_type: Mapped[str] = mapped_column(
        Enum("fixed", "variable", "mixed", name="interest_type_enum", create_type=False),
        nullable=False,
        default="fixed",
    )

    term_months: Mapped[int] = mapped_column(nullable=False)
    payment_frequency: Mapped[str] = mapped_column(
        Enum("monthly", "bi_weekly", "weekly", name="payment_frequency_enum", create_type=False),
        nullable=False,
        default="monthly",
    )
    monthly_payment: Mapped[Decimal] = mapped_column(
        Numeric(precision=19, scale=4), nullable=False
    )

    total_paid: Mapped[Decimal] = mapped_column(
        Numeric(precision=19, scale=4), nullable=False, default=0
    )
    total_interest_paid: Mapped[Decimal] = mapped_column(
        Numeric(precision=19, scale=4), nullable=False, default=0
    )
    total_interest_expected: Mapped[Decimal] = mapped_column(
        Numeric(precision=19, scale=4), nullable=False, default=0
    )

    disbursement_date: Mapped[date | None] = mapped_column(nullable=True, default=None)
    first_payment_date: Mapped[date | None] = mapped_column(nullable=True, default=None)
    next_payment_date: Mapped[date | None] = mapped_column(nullable=True, default=None)
    final_payment_date: Mapped[date | None] = mapped_column(nullable=True, default=None)
    paid_off_date: Mapped[date | None] = mapped_column(nullable=True, default=None)

    status: Mapped[str] = mapped_column(
        Enum(
            "pending",
            "active",
            "paid_off",
            "defaulted",
            "refinanced",
            "suspended",
            "cancelled",
            name="loan_status_enum",
            create_type=False,
        ),
        nullable=False,
        default="pending",
    )

    penalty_rate_monthly: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=8, scale=4), nullable=True, default=None
    )
    grace_period_days: Mapped[int] = mapped_column(nullable=False, default=0)
    early_payoff_allowed: Mapped[bool] = mapped_column(nullable=False, default=True)
    early_payoff_penalty_pct: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=8, scale=4), nullable=True, default=None
    )

    metadata_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    notes: Mapped[str | None] = mapped_column(String(1000), nullable=True, default=None)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )

    # relationships
    user: Mapped[UserModel] = relationship(back_populates="loans", lazy="noload")  # type: ignore[name-defined]
    payments: Mapped[list[LoanPaymentModel]] = relationship(  # type: ignore[name-defined]
        back_populates="loan", lazy="selectin", cascade="all, delete-orphan"
    )
    amortization_entries: Mapped[list[LoanAmortizationEntryModel]] = relationship(  # type: ignore[name-defined]
        back_populates="loan", lazy="selectin", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_loan_user_status", "user_id", "status"),
        Index("ix_loan_user_type", "user_id", "loan_type"),
    )

    def __repr__(self) -> str:
        return f"<Loan {self.name} | {self.loan_type} | balance={self.current_balance}>"
