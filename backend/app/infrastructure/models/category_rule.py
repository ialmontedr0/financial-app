"""Category Rule model - pattern matching for auto-classification."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.base import Base

if TYPE_CHECKING:
    from app.infrastructure.models.category import CategoryModel
    from app.infrastructure.models.subcategory import SubcategoryModel
    from app.infrastructure.models.user import UserModel


class CategoryRuleModel(Base):
    """Rule for automatic transaction categorization."""

    __tablename__ = "category_rule"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=True,  # NULL = system rule
        index=True,
    )

    # --- Rule Identity ---
    rule_name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)

    # --- Pattern ---
    pattern_type: Mapped[str] = mapped_column(
        String(30), nullable=False, default="keyword"
    )  # keyword, regex, amount_range, merchant_exact
    pattern: Mapped[str] = mapped_column(Text, nullable=False)
    # keyword: "walmart|colmado|super" (pipe-separated)
    # regex: "\\b(ATM|CAJERO)\\b"
    # merchant_exact: "NETFLIX"
    # amount_range: ignored (use min/max)

    # --- Amount Range (for amount_range pattern_type) ---
    amount_min: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=19, scale=4), nullable=True, default=None
    )
    amount_max: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=19, scale=4), nullable=True, default=None
    )

    # --- Target ---
    target_category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("category.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    target_subcategory_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("subcategory.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
    )

    # --- Settings ---
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # --- Stats ---
    hit_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # --- Timestamps ---
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(),
        nullable=False,
    )

    # --- Relationships ---
    user: Mapped[UserModel | None] = relationship(
        "UserModel", lazy="noload"
    )
    target_category: Mapped[CategoryModel] = relationship(
        "CategoryModel", lazy="selectin"
    )
    target_subcategory: Mapped[SubcategoryModel | None] = relationship(
        "SubcategoryModel", lazy="selectin"
    )

    def __repr__(self) -> str:
        return (
            f"<CategoryRuleModel(id={self.id}, name={self.rule_name}, "
            f"pattern={self.pattern_type})>"
        )
