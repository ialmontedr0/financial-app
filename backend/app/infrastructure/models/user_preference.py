"""User preferences model — currency, timezone, language, formatting, notifications."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.base import Base

if TYPE_CHECKING:

    from app.infrastructure.models.user import UserModel


class UserPreferenceModel(Base):
    """User preferences — 1:1 with UserModel."""

    __tablename__ = "user_preference"

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

    # --- Localization ---
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False, default="DOP")
    timezone: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="America/Santo_Domingo",
    )
    language: Mapped[str] = mapped_column(String(5), nullable=False, default="es")

    # --- Formatting ---
    date_format: Mapped[str] = mapped_column(String(20), nullable=False, default="DD/MM/YYYY")
    time_format: Mapped[str] = mapped_column(
        Enum("12h", "24h", name="time_format_type", create_type=False),
        nullable=False,
        default="24h",
    )
    number_format: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="#,##0.00",
    )
    first_day_of_week: Mapped[str] = mapped_column(
        Enum("monday", "sunday", name="week_start_type", create_type=False),
        nullable=False,
        default="monday",
    )

    # --- Appearance ---
    theme: Mapped[str] = mapped_column(
        Enum("light", "dark", "system", name="theme_type", create_type=False),
        nullable=False,
        default="system",
    )

    # --- Notifications ---
    email_notifications: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    push_notifications: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    marketing_emails: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

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
    user: Mapped[UserModel] = relationship("UserModel", back_populates="preferences")

    def __repr__(self) -> str:
        return (
            f"<UserPreferenceModel(id={self.id}, user_id={self.user_id}, "
            f"currency={self.currency_code}, tz={self.timezone})>"
        )
