"""Use case: Get category usage statistics."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.category_repository import CategoryRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class GetCategoryStatsUseCase:
    """Get category usage statistics (for future analytics)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = CategoryRepository(session)

    async def execute(self, user_id: uuid.UUID) -> dict:
        """Return category stats (placeholder — will be real data in Phase 7+)."""
        categories = await self._repo.list_categories(user_id)

        return {
            "total_categories": len(categories),
            "system_categories": sum(1 for c in categories if c.is_system),
            "user_categories": sum(1 for c in categories if not c.is_system),
            "by_type": {
                "expense": sum(1 for c in categories if c.category_type == "expense"),
                "income": sum(1 for c in categories if c.category_type == "income"),
                "transfer": sum(1 for c in categories if c.category_type == "transfer"),
                "adjustment": sum(1 for c in categories if c.category_type == "adjustment"),
            },
        }
