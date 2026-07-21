"""Use case: Get spending trends by category."""

from __future__ import annotations

import uuid

import structlog

if __name__ != "__main__":
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class GetHabitTrendsUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(self, user_id: uuid.UUID, months: int = 6) -> dict:
        """Get spending trends by category."""
        from app.ai.recommendations.habit_analyzer import HabitAnalyzer

        analyzer = HabitAnalyzer()
        return await analyzer.get_trends(self._session, user_id, months=months)
