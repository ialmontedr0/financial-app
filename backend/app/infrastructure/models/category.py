"""Category model - transaction classification."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.base import Base

if TYPE_CHECKING:
    from app.infrastructure.models.subcategory import SubcategoryModel
    from app.infrastructure.models.user import UserModel


class CategoryModel(Base):
    """Category for classifying transactions."""

    __tablename__ = "category"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=True,  # NULL = system category
        index=True,
    )

    # --- Identity ---
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    category_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="expense"
    )

    # --- Scope ---
    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # --- Display ---
    icon: Mapped[str | None] = mapped_column(String(50), nullable=True, default=None)
    color: Mapped[str | None] = mapped_column(String(7), nullable=True, default=None)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # --- AI Metadata ---
    keywords: Mapped[str | None] = mapped_column(
        Text, nullable=True, default=None
    )  # comma-separated keywords for quick matching

    # --- Timestamps ---
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(),
        nullable=False,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )

    # --- Relationships ---
    user: Mapped[UserModel | None] = relationship(
        "UserModel", back_populates="categories", lazy="noload"
    )
    subcategories: Mapped[list[SubcategoryModel]] = relationship(
        "SubcategoryModel",
        back_populates="category",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<CategoryModel(id={self.id}, name={self.name}, "
            f"type={self.category_type}, system={self.is_system})>"
        )
