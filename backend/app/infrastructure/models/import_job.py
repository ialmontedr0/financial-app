"""ImportJob model — tracks file import status and results."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base


class ImportJobModel(Base):
    __tablename__ = "import_job"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(10), nullable=False)
    import_type: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")

    total_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    processed_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    valid_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    skipped_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    errors: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    preview_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    mapping_config: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"<ImportJobModel(id={self.id}, file={self.file_name}, status={self.status})>"
