"""Income model - stores income-specific metadata linked to a transaction."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.base import Base

if TYPE_CHECKING:
    from app.infrastructure.models.income_source import IncomeSourceModel
    from app.infrastructure.models.transaction import TransactionModel
    from app.infrastructure.models.user import UserModel


class IncomeModel(Base):
    """Extended income metadata linked to a TransactionModel."""

    __tablename__ = "income"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    transaction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("transaction.id", ondelete="CASCADE"), nullable=False, unique=True, index=True,
    )

    # --- Income Metadata ---
    income_type: Mapped[str] = mapped_column(String(20), nullable=False, default="salary")
    income_status: Mapped[str] = mapped_column(String(20), nullable=False, default="received")
    stability: Mapped[str] = mapped_column(String(20), nullable=False, default="fixed")

    # --- Source (optional) ---
    income_source_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("income_source.id", ondelete="SET NULL"), nullable=True, default=None, index=True,
    )

    # --- Employer / Payer Info ---
    employer_name: Mapped[str | None] = mapped_column(String(200), nullable=True, default=None)
    employer_tax_id: Mapped[str | None] = mapped_column(String(50), nullable=True, default=None)

    # --- Tax ---
    gross_amount: Mapped[Decimal | None] = mapped_column(Numeric(precision=19, scale=4), nullable=True, default=None)
    tax_withheld: Mapped[Decimal | None] = mapped_column(Numeric(precision=19, scale=4), nullable=True, default=None)
    net_amount: Mapped[Decimal | None] = mapped_column(Numeric(precision=19, scale=4), nullable=True, default=None)

    # --- Frequency (for recurring income tracking) ---
    frequency: Mapped[str | None] = mapped_column(String(20), nullable=True, default=None)

    # --- Effective ---
    effective_date: Mapped[date] = mapped_column(Date, nullable=False)

    # --- Notes ---
    notes: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)

    # --- Timestamps ---
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)

    # --- Relationships ---
    user: Mapped[UserModel] = relationship("UserModel", lazy="noload")
    transaction: Mapped[TransactionModel] = relationship("TransactionModel", lazy="selectin")
    income_source: Mapped[IncomeSourceModel | None] = relationship("IncomeSourceModel", lazy="selectin")

    def __repr__(self) -> str:
        return f"<IncomeModel(id={self.id}, type={self.income_type}, status={self.income_status})>"
