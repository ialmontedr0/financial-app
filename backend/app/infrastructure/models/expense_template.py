"""Expense Template model - reusable expense templates for quick entry."""

from __future__ import annotations

import uuid
from datetime import datetime  # noqa: TC003
from decimal import Decimal  # noqa: TC003
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.base import Base

if TYPE_CHECKING:
    from app.infrastructure.models.category import CategoryModel
    from app.infrastructure.models.financial_account import FinancialAccountModel
    from app.infrastructure.models.subcategory import SubcategoryModel
    from app.infrastructure.models.user import UserModel


class ExpenseTemplateModel(Base):
    """Reusable expense template for quick expense creation."""

    __tablename__ = "expense_template"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # --- Identity ---
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # --- Defaults ---
    default_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=19, scale=4), nullable=True, default=None
    )
    default_currency: Mapped[str] = mapped_column(String(3), nullable=False, default="DOP")
    default_account_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("financial_account.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
    )
    default_category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("category.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
    )
    default_subcategory_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("subcategory.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
    )
    default_notes: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    default_source: Mapped[str] = mapped_column(String(20), nullable=False, default="template")

    # --- Schedule (optional) ---
    default_frequency: Mapped[str | None] = mapped_column(
        String(20), nullable=True, default=None
    )  # if this is recurring

    # --- Stats ---
    usage_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )

    # --- Display ---
    icon: Mapped[str | None] = mapped_column(String(500), nullable=True, default=None)
    color: Mapped[str | None] = mapped_column(String(7), nullable=True, default=None)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

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
    default_account: Mapped[FinancialAccountModel | None] = relationship(
        "FinancialAccountModel", lazy="selectin"
    )
    default_category: Mapped[CategoryModel | None] = relationship("CategoryModel", lazy="selectin")
    default_subcategory: Mapped[SubcategoryModel | None] = relationship(
        "SubcategoryModel", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<ExpenseTemplateModel(id={self.id}, name={self.name}, usage={self.usage_count})>"
