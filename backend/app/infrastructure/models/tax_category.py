from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.base import Base

if TYPE_CHECKING:  # pragma: no cover
    from app.infrastructure.models.tax_deduction import TaxDeductionModel
    from app.infrastructure.models.user import UserModel


class TaxCategoryModel(Base):
    __tablename__ = "tax_category"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    tax_year: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # relationships
    user: Mapped[UserModel] = relationship("UserModel", lazy="noload")
    deductions: Mapped[list[TaxDeductionModel]] = relationship(
        back_populates="category", lazy="selectin", passive_deletes=True
    )

    __table_args__ = (Index("ix_tax_category_user_year", "user_id", "tax_year"),)

    def __repr__(self) -> str:
        return f"<TaxCategory {self.name} | year={self.tax_year}>"
