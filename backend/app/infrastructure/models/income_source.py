"""Income Source model - represents where income comes from."""

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
    from app.infrastructure.models.category import CategoryModel
    from app.infrastructure.models.financial_account import FinancialAccountModel
    from app.infrastructure.models.user import UserModel


class IncomeSourceModel(Base):
    """Represents a source of income (employer, freelance client, investment, etc)."""

    __tablename__ = "income_source"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True,
    )

    # --- Identity ---
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)

    # --- Classification ---
    income_type: Mapped[str] = mapped_column(String(20), nullable=False, default="salary")
    stability: Mapped[str] = mapped_column(String(20), nullable=False, default="fixed")
    tax_id: Mapped[str | None] = mapped_column(String(50), nullable=True, default=None)

    # --- Defaults ---
    default_amount: Mapped[Decimal | None] = mapped_column(Numeric(precision=19, scale=4), nullable=True, default=None)
    default_account_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("financial_account.id", ondelete="SET NULL"), nullable=True, default=None,
    )
    default_category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("category.id", ondelete="SET NULL"), nullable=True, default=None,
    )
    default_currency: Mapped[str] = mapped_column(String(3), nullable=False, default="DOP")
    frequency: Mapped[str | None] = mapped_column(String(20), nullable=True, default=None)
    pay_day: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)

    # --- Stats ---
    total_received: Mapped[Decimal] = mapped_column(
        Numeric(precision=19, scale=4), nullable=False, server_default="0",
    )
    income_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)

    # --- Status ---
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # --- Display ---
    icon: Mapped[str | None] = mapped_column(String(500), nullable=True, default=None)
    color: Mapped[str | None] = mapped_column(String(7), nullable=True, default=None)

    # --- Timestamps ---
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)

    # --- Relationships ---
    user: Mapped[UserModel] = relationship("UserModel", lazy="noload")
    default_account: Mapped[FinancialAccountModel | None] = relationship("FinancialAccountModel", lazy="selectin")
    default_category: Mapped[CategoryModel | None] = relationship("CategoryModel", lazy="selectin")

    def __repr__(self) -> str:
        return f"<IncomeSourceModel(id={self.id}, name={self.name}, type={self.income_type})>"
