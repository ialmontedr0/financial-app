from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.base import Base

if TYPE_CHECKING:  # pragma: no cover
    from app.infrastructure.models.tax_category import TaxCategoryModel
    from app.infrastructure.models.user import UserModel


class TaxDeductionModel(Base):
    __tablename__ = "tax_deduction"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tax_category.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
        index=True,
    )
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(precision=19, scale=4), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    deductible: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=19, scale=4), nullable=True, default=None
    )
    tax_year: Mapped[int] = mapped_column(Integer, nullable=False)
    receipt_url: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # relationships
    user: Mapped[UserModel] = relationship("UserModel", lazy="noload")
    category: Mapped[TaxCategoryModel | None] = relationship(
        back_populates="deductions", lazy="selectin"
    )

    __table_args__ = (Index("ix_tax_deduction_user_year", "user_id", "tax_year"),)

    def __repr__(self) -> str:
        return f"<TaxDeduction {self.description} | {self.amount} | {self.date}>"
