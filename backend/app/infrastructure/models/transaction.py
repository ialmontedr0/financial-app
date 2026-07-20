"""Transaction model - the core financial event."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, Index, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.base import Base

if TYPE_CHECKING:
    from app.infrastructure.models.category import CategoryModel
    from app.infrastructure.models.financial_account import FinancialAccountModel
    from app.infrastructure.models.subcategory import SubcategoryModel
    from app.infrastructure.models.transaction_attachment import TransactionAttachmentModel
    from app.infrastructure.models.transaction_audit_log import TransactionAuditLogModel
    from app.infrastructure.models.transaction_recurring import TransactionRecurringModel
    from app.infrastructure.models.transaction_tag import TransactionTagModel
    from app.infrastructure.models.user import UserModel


class TransactionModel(Base):
    """Transaction - the fundamental financial event."""

    __tablename__ = "transaction"
    __table_args__ = (
        Index("ix_transaction_user_effective", "user_id", "effective_date"),
        Index("ix_transaction_user_type", "user_id", "transaction_type"),
        Index("ix_transaction_transfer_id", "transfer_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("financial_account.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("category.id", ondelete="SET NULL"), nullable=True, default=None,
    )
    subcategory_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("subcategory.id", ondelete="SET NULL"), nullable=True, default=None,
    )

    transaction_type: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="completed")

    amount: Mapped[Decimal] = mapped_column(Numeric(precision=19, scale=4), nullable=False)
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False, default="DOP")

    description: Mapped[str] = mapped_column(Text, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)

    effective_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    created_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )

    transfer_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, default=None)

    source: Mapped[str] = mapped_column(String(20), nullable=False, default="manual")

    recurring_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("transaction_recurring.id", ondelete="SET NULL"), nullable=True, default=None,
    )

    ai_category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("category.id", ondelete="SET NULL"), nullable=True, default=None,
    )
    ai_confidence: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=5, scale=4), nullable=True, default=None,
    )
    ai_model_version: Mapped[str | None] = mapped_column(String(50), nullable=True, default=None)
    ai_reason: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)

    user: Mapped[UserModel] = relationship("UserModel", foreign_keys=[user_id], lazy="noload")
    account: Mapped[FinancialAccountModel] = relationship("FinancialAccountModel", lazy="selectin")
    category: Mapped[CategoryModel | None] = relationship("CategoryModel", foreign_keys=[category_id], lazy="selectin")
    subcategory: Mapped[SubcategoryModel | None] = relationship("SubcategoryModel", lazy="selectin")
    recurring: Mapped[TransactionRecurringModel | None] = relationship("TransactionRecurringModel", lazy="noload")
    tags: Mapped[list[TransactionTagModel]] = relationship(
        "TransactionTagModel", back_populates="transaction", lazy="selectin", cascade="all, delete-orphan",
    )
    attachments: Mapped[list[TransactionAttachmentModel]] = relationship(
        "TransactionAttachmentModel", back_populates="transaction", lazy="selectin", cascade="all, delete-orphan",
    )
    audit_logs: Mapped[list[TransactionAuditLogModel]] = relationship(
        "TransactionAuditLogModel", back_populates="transaction", lazy="noload",
    )

    def __repr__(self) -> str:
        return f"<TransactionModel(id={self.id}, type={self.transaction_type}, amount={self.amount} {self.currency_code}, status={self.status})>"
