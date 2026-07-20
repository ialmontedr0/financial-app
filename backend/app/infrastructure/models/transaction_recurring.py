"""Transaction Recurring model - recurring transaction patterns."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.base import Base

if TYPE_CHECKING:
    from app.infrastructure.models.category import CategoryModel
    from app.infrastructure.models.financial_account import FinancialAccountModel
    from app.infrastructure.models.subcategory import SubcategoryModel
    from app.infrastructure.models.user import UserModel


class TransactionRecurringModel(Base):
    __tablename__ = "transaction_recurring"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("financial_account.id", ondelete="CASCADE"), nullable=False,
    )
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("category.id", ondelete="SET NULL"), nullable=True, default=None,
    )
    subcategory_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("subcategory.id", ondelete="SET NULL"), nullable=True, default=None,
    )

    transaction_type: Mapped[str] = mapped_column(String(20), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(precision=19, scale=4), nullable=False)
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False, default="DOP")
    description: Mapped[str] = mapped_column(Text, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)

    frequency: Mapped[str] = mapped_column(String(20), nullable=False)
    interval: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True, default=None)
    next_execution_date: Mapped[date] = mapped_column(Date, nullable=False)

    max_executions: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)
    execution_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)

    user: Mapped[UserModel] = relationship("UserModel", lazy="noload")
    account: Mapped[FinancialAccountModel] = relationship("FinancialAccountModel", lazy="selectin")
    category: Mapped[CategoryModel | None] = relationship("CategoryModel", lazy="selectin")
    subcategory: Mapped[SubcategoryModel | None] = relationship("SubcategoryModel", lazy="selectin")

    def __repr__(self) -> str:
        return f"<TransactionRecurringModel(id={self.id}, freq={self.frequency}, next={self.next_execution_date}, active={self.is_active})>"
