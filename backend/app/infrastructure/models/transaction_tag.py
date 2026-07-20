"""Transaction Tag model - many-to-many tags for transactions."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.base import Base

if TYPE_CHECKING:
    from app.infrastructure.models.transaction import TransactionModel
    from app.infrastructure.models.user import UserModel


class TransactionTagModel(Base):
    __tablename__ = "transaction_tag"
    __table_args__ = (UniqueConstraint("transaction_id", "tag_name", name="uq_transaction_tag"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("transaction.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    tag_name: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    transaction: Mapped[TransactionModel] = relationship("TransactionModel", back_populates="tags", lazy="noload")
    user: Mapped[UserModel] = relationship("UserModel", lazy="noload")

    def __repr__(self) -> str:
        return f"<TransactionTagModel(tx={self.transaction_id}, tag={self.tag_name})>"
