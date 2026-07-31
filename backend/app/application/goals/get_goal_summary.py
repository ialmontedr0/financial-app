"""Use case: Get goals summary dashboard."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.goal_repository import GoalRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class GetGoalSummaryUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = GoalRepository(session)

    async def execute(self, user_id: uuid.UUID) -> dict:
        goals = await self._repo.list_goals(user_id)
        for g in goals:
            previous_pct = g.milestone_reached_pct
            refreshed = await self._repo.recalculate_progress(g.id, user_id)
            if refreshed is None:
                continue
            g = refreshed
            target = float(g.target_amount)
            current = float(g.current_amount)
            pct = round((current / target * 100), 2) if target > 0 else 0.0

            from app.application.goals.notifications import emit_goal_milestone_notifications

            await emit_goal_milestone_notifications(
                self._session,
                user_id,
                goal_id=g.id,
                goal_name=g.name,
                current_amount=current,
                target_amount=target,
                previous_pct=previous_pct,
                current_pct=pct,
            )
        return await self._repo.get_goals_summary(user_id)
