"""Income Schedule model - projected/scheduled future income."""

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
    from app.infrastructure.models.financial_account import FinancialAccountModel
    from app.infrastructure.models.income_source import IncomeSourceModel
    from app.infrastructure.models.user import UserModel


class IncomeScheduleModel(Base):
    """Projected or scheduled future income."""

    __tablename__ = "income_schedule"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True,
    )

    # --- Identity ---
    description: Mapped[str] = mapped_column(String(500), nullable=False)

    # --- Financial ---
    amount: Mapped[Decimal] = mapped_column(Numeric(precision=19, scale=4), nullable=False)
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False, default="DOP")

    # --- Account ---
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("financial_account.id", ondelete="CASCADE"), nullable=False, index=True,
    )

    # --- Source ---
    income_source_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("income_source.id", ondelete="SET NULL"), nullable=True, default=None,
    )

    # --- Schedule ---
    expected_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="projected")
    frequency: Mapped[str | None] = mapped_column(String(20), nullable=True, default=None)

    # --- Projection ---
    projection_method: Mapped[str | None] = mapped_column(String(20), nullable=True, default=None)
    confidence_score: Mapped[Decimal | None] = mapped_column(Numeric(precision=5, scale=4), nullable=True, default=None)

    # --- Notes ---
    notes: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)

    # --- Execution ---
    received_transaction_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("transaction.id", ondelete="SET NULL"), nullable=True, default=None,
    )
    received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)

    # --- Timestamps ---
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)

    # --- Relationships ---
    user: Mapped[UserModel] = relationship("UserModel", lazy="noload")
    account: Mapped[FinancialAccountModel] = relationship("FinancialAccountModel", lazy="selectin")
    income_source: Mapped[IncomeSourceModel | None] = relationship("IncomeSourceModel", lazy="selectin")

    def __repr__(self) -> str:
        return f"<IncomeScheduleModel(id={self.id}, desc={self.description}, date={self.expected_date}, amount={self.amount})>"
