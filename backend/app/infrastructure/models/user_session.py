import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base


class UserSessionModel(Base):
    """ORM model for tracking user sessions across devices."""

    __tablename__ = "user_session"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    device_info: Mapped[str] = mapped_column(String(500), nullable=False)
    ip_address: Mapped[str] = mapped_column(String(45), nullable=False)  # IPv6 max 45 chars
    user_agent: Mapped[str] = mapped_column(String(500), nullable=False)
    refresh_token_jti: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    def __repr__(self) -> str:
        return (
            f"<UserSessionModel(id={self.id}, user_id={self.user_id}, revoked={self.is_revoked})>"
        )
