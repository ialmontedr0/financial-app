from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.base import Base

if TYPE_CHECKING:
    from app.infrastructure.models.user import UserModel


class UserProfileModel(Base):
    """Extended user profile — 1:1 with UserModel."""

    __tablename__ = "user_profile"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )

    # --- Personal Info ---
    first_name: Mapped[str | None] = mapped_column(String(100), nullable=True, default=None)
    last_name: Mapped[str | None] = mapped_column(String(100), nullable=True, default=None)
    display_name: Mapped[str | None] = mapped_column(String(200), nullable=True, default=None)
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True, default=None)
    gender: Mapped[str | None] = mapped_column(
        Enum("male", "female", "other", "prefer_not_to_say", name="user_gender", create_type=False),
        nullable=True,
        default=None,
    )
    bio: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)

    # --- Contact ---
    phone_secondary: Mapped[str | None] = mapped_column(String(50), nullable=True, default=None)

    # --- Address ---
    address_line1: Mapped[str | None] = mapped_column(String(255), nullable=True, default=None)
    address_line2: Mapped[str | None] = mapped_column(String(255), nullable=True, default=None)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True, default=None)
    state_province: Mapped[str | None] = mapped_column(String(100), nullable=True, default=None)
    country_code: Mapped[str | None] = mapped_column(String(2), nullable=True, default=None)
    postal_code: Mapped[str | None] = mapped_column(String(20), nullable=True, default=None)

    # --- Timestamps ---
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # --- Relationship ---
    user: Mapped[UserModel] = relationship("UserModel", back_populates="profile")

    def __repr__(self) -> str:
        return (
            f"<UserProfileModel(id={self.id}, user_id={self.user_id}, "
            f"name={self.first_name} {self.last_name})>"
        )
