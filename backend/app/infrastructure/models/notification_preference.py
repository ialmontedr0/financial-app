from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.base import Base


class NotificationPreferenceModel(Base):
    __tablename__ = "notification_preference"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("user.id"), unique=True, nullable=False)

    email_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    push_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    telegram_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    discord_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    webhook_enabled: Mapped[bool] = mapped_column(Boolean, default=False)

    email_types: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    push_types: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    telegram_types: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    discord_types: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    webhook_types: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    telegram_chat_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    discord_webhook_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    webhook_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    webhook_secret: Mapped[str | None] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user = relationship("UserModel", back_populates="notification_preferences")
