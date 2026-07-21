"""Automation Rule model - user-defined IF/THEN financial automations."""

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
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.base import Base

if TYPE_CHECKING:
    from app.infrastructure.models.user import UserModel


class AutomationRuleModel(Base):
    """User-defined automation rule with IF/THEN structure."""

    __tablename__ = "automation_rule"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)

    trigger_type: Mapped[str] = mapped_column(String(30), nullable=False)
    trigger_conditions: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)

    action_type: Mapped[str] = mapped_column(String(30), nullable=False)
    action_params: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)

    max_executions_per_month: Mapped[int | None] = mapped_column(
        Integer, nullable=True, default=None
    )
    min_balance_required: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=19, scale=4), nullable=True, default=None
    )

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    execution_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_executed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    last_execution_status: Mapped[str | None] = mapped_column(
        String(20), nullable=True, default=None
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )

    user: Mapped[UserModel] = relationship("UserModel", lazy="noload")

    def __repr__(self) -> str:
        return (
            f"<AutomationRule(id={self.id}, name={self.name}, "
            f"trigger={self.trigger_type}, action={self.action_type}, "
            f"active={self.is_active})>"
        )
