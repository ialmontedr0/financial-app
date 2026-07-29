from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Index, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.base import Base

if TYPE_CHECKING:
    from app.infrastructure.models.credit_purchase import CreditPurchaseModel


class CreditPurchaseInstallmentModel(Base):
    __tablename__ = "credit_purchase_installment"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    purchase_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("credit_purchase.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )

    installment_number: Mapped[int] = mapped_column(nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(precision=19, scale=4), nullable=False)
    principal_portion: Mapped[Decimal] = mapped_column(
        Numeric(precision=19, scale=4), nullable=False, default=0
    )
    interest_portion: Mapped[Decimal] = mapped_column(
        Numeric(precision=19, scale=4), nullable=False, default=0
    )
    balance_after: Mapped[Decimal] = mapped_column(
        Numeric(precision=19, scale=4), nullable=False, default=0
    )
    status: Mapped[str] = mapped_column(
        Enum("pending", "paid", "late", name="installment_status_enum", create_type=False),
        nullable=False, default="pending",
    )
    paid_at: Mapped[date | None] = mapped_column(Date, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    purchase: Mapped[CreditPurchaseModel] = relationship(back_populates="installments", lazy="noload")

    __table_args__ = (
        Index("ix_installment_purchase_number", "purchase_id", "installment_number", unique=True),
    )

    def __repr__(self) -> str:
        return f"<Installment #{self.installment_number} | ${self.amount} | {self.status}>"
