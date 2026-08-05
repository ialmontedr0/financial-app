"""DomainEvent model - durable audit log for events processed by the worker."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Index, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base


class DomainEventModel(Base):
    """Durable record of domain events processed by the event bus worker."""

    __tablename__ = "domain_event"
    __table_args__ = (Index("ix_domain_event_type_status", "event_type", "status"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    aggregate_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    aggregate_type: Mapped[str] = mapped_column(String(50), nullable=False)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True, default=None
    )
    data: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True, default=None)

    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="published")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )

    def __repr__(self) -> str:
        return f"<DomainEvent(id={self.id}, event_type={self.event_type}, status={self.status})>"
