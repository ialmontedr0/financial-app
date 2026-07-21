"""Use case: Analyze user spending habits."""

from __future__ import annotations

import uuid

import structlog

if __name__ != "__main__":
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class AnalyzeHabitsUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(self, user_id: uuid.UUID, months: int = 6) -> dict:
        """Analyze spending habits and return insights."""
        from app.ai.recommendations.habit_analyzer import HabitAnalyzer

        analyzer = HabitAnalyzer()
        result = await analyzer.analyze(self._session, user_id, months=months)

        return {
            "habits": result,
            "overall_habit_score": result.get("overall_habit_score", 0),
            "total_recommendations": len(result.get("recommendations", [])),
        }
