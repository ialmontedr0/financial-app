from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Index, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.base import Base

if TYPE_CHECKING:  # pragma: no cover
    from app.infrastructure.models.insurance import InsuranceModel


class InsurancePremiumModel(Base):
    __tablename__ = "insurance_premium"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    insurance_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("insurance.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(precision=19, scale=4), nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    paid_date: Mapped[date | None] = mapped_column(Date, nullable=True, default=None)
    status: Mapped[str] = mapped_column(
        Enum(
            "pending",
            "paid",
            "overdue",
            "cancelled",
            name="premium_status_enum",
            create_type=False,
        ),
        nullable=False,
        default="pending",
    )
    payment_method: Mapped[str | None] = mapped_column(String(100), nullable=True, default=None)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # relationships
    insurance: Mapped[InsuranceModel] = relationship(back_populates="premiums", lazy="noload")

    __table_args__ = (Index("ix_insurance_premium_due_date", "insurance_id", "due_date"),)

    def __repr__(self) -> str:
        return f"<InsurancePremium {self.amount} | due={self.due_date} | {self.status}>"
