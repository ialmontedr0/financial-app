"""Repository for import_job operations."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.models.import_job import ImportJobModel


class ImportRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, data: dict[str, Any]) -> ImportJobModel:
        job = ImportJobModel(**data)
        self.db.add(job)
        await self.db.flush()
        return job

    async def get_by_id_and_user(self, job_id: uuid.UUID, user_id: uuid.UUID) -> ImportJobModel | None:
        result = await self.db.execute(
            select(ImportJobModel).where(
                ImportJobModel.id == job_id,
                ImportJobModel.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_by_user(
        self, user_id: uuid.UUID, skip: int = 0, limit: int = 20
    ) -> list[ImportJobModel]:
        result = await self.db.execute(
            select(ImportJobModel)
            .where(ImportJobModel.user_id == user_id)
            .order_by(ImportJobModel.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update_status(
        self,
        job: ImportJobModel,
        status: str,
        **extra: Any,
    ) -> None:
        job.status = status
        for key, value in extra.items():
            setattr(job, key, value)
        if status in ("completed", "failed"):
            job.completed_at = datetime.now(UTC)
        await self.db.flush()
