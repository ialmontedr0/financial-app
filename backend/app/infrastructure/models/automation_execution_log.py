"""Automation Execution Log - audit trail for every automation execution."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.base import Base

if TYPE_CHECKING:
    from app.infrastructure.models.automation_rule import AutomationRuleModel
    from app.infrastructure.models.user import UserModel


class AutomationExecutionLogModel(Base):
    """Audit log for every automation rule execution attempt."""

    __tablename__ = "automation_execution_log"
    __table_args__ = (
        Index("ix_auto_exec_log_rule", "rule_id", "executed_at"),
        Index("ix_auto_exec_log_user", "user_id", "executed_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    rule_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("automation_rule.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(String(20), nullable=False)

    trigger_snapshot: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    action_result: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    amount_involved: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=19, scale=4), nullable=True
    )

    source_account_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    target_account_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )

    is_dry_run: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    executed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped[UserModel] = relationship("UserModel", lazy="noload")
    rule: Mapped[AutomationRuleModel] = relationship("AutomationRuleModel", lazy="noload")

    def __repr__(self) -> str:
        return (
            f"<AutomationExecLog(id={self.id}, rule={self.rule_id}, "
            f"status={self.status}, at={self.executed_at})>"
        )
