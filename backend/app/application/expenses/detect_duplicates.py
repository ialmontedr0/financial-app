"""Use case: Detect potential duplicate expenses."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.expense_repository import ExpenseRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class DetectDuplicatesUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = ExpenseRepository(session)

    async def execute(self, user_id: uuid.UUID, *, days: int = 30) -> dict:
        if days < 1 or days > 365:
            days = 30

        duplicates = await self._repo.detect_duplicates(user_id, days=days)

        return {
            "duplicate_groups": len(duplicates),
            "total_potential_duplicates": sum(d["count"] for d in duplicates),
            "groups": duplicates,
            "period_days": days,
        }
