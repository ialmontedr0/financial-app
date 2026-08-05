from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Index, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.base import Base

if TYPE_CHECKING:
    from app.infrastructure.models.credit_purchase_installment import CreditPurchaseInstallmentModel


class CreditPurchaseModel(Base):
    __tablename__ = "credit_purchase"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True
    )

    item_name: Mapped[str] = mapped_column(String(200), nullable=False)
    store_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    total_price: Mapped[Decimal] = mapped_column(Numeric(precision=19, scale=4), nullable=False)
    down_payment: Mapped[Decimal] = mapped_column(
        Numeric(precision=19, scale=4), nullable=False, default=0
    )
    financed_amount: Mapped[Decimal] = mapped_column(Numeric(precision=19, scale=4), nullable=False)

    annual_interest_rate: Mapped[Decimal] = mapped_column(
        Numeric(precision=8, scale=4), nullable=False, default=0
    )
    installment_count: Mapped[int] = mapped_column(nullable=False)
    installment_frequency: Mapped[str] = mapped_column(
        Enum(
            "weekly",
            "biweekly",
            "monthly",
            "quarterly",
            "quadrimensual",
            "semestral",
            "annual",
            name="installment_frequency_enum",
            create_type=False,
        ),
        nullable=False,
        default="monthly",
    )
    installment_amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=19, scale=4), nullable=False
    )
    calculation_method: Mapped[str] = mapped_column(String(10), nullable=False, default="auto")

    total_interest: Mapped[Decimal] = mapped_column(
        Numeric(precision=19, scale=4), nullable=False, default=0
    )
    total_paid: Mapped[Decimal] = mapped_column(
        Numeric(precision=19, scale=4), nullable=False, default=0
    )

    purchase_date: Mapped[date] = mapped_column(Date, nullable=False)
    first_due_date: Mapped[date] = mapped_column(Date, nullable=False)

    status: Mapped[str] = mapped_column(
        Enum(
            "active",
            "completed",
            "cancelled",
            "defaulted",
            name="credit_purchase_status_enum",
            create_type=False,
        ),
        nullable=False,
        default="active",
    )

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )

    installments: Mapped[list[CreditPurchaseInstallmentModel]] = relationship(
        back_populates="purchase",
        lazy="selectin",
        cascade="all, delete-orphan",
        order_by="CreditPurchaseInstallmentModel.installment_number",
    )

    __table_args__ = (Index("ix_credit_purchase_user_status", "user_id", "status"),)

    def __repr__(self) -> str:
        return f"<CreditPurchase {self.item_name} | {self.store_name} | ${self.financed_amount}>"
