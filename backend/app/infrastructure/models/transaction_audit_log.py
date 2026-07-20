"""Transaction Audit Log model - immutable history of changes."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.base import Base

if TYPE_CHECKING:
    from app.infrastructure.models.transaction import TransactionModel
    from app.infrastructure.models.user import UserModel


class TransactionAuditLogModel(Base):
    __tablename__ = "transaction_audit_log"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("transaction.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    action: Mapped[str] = mapped_column(String(20), nullable=False)
    changes: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True, default=None)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    transaction: Mapped[TransactionModel] = relationship("TransactionModel", back_populates="audit_logs", lazy="noload")
    user: Mapped[UserModel] = relationship("UserModel", lazy="noload")

    def __repr__(self) -> str:
        return f"<TransactionAuditLogModel(id={self.id}, action={self.action}, tx={self.transaction_id})>"
