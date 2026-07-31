"""Use case: Refresh goal progress and prediction."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.goal_repository import GoalRepository

if TYPE_CHECKING:
    import uuid
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class RefreshGoalUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = GoalRepository(session)

    async def execute(self, user_id: uuid.UUID, goal_id: uuid.UUID) -> dict:
        from app.middleware.error_handler import NotFoundError

        goal = await self._repo.get_goal_by_id(goal_id, user_id)
        if goal is None:
            raise NotFoundError("Goal")
        previous_pct = goal.milestone_reached_pct

        goal = await self._repo.recalculate_progress(goal_id, user_id)
        if goal is None:
            raise NotFoundError("Goal")

        progress = await self._repo.get_goal_progress(goal_id, user_id)

        from app.application.goals.create_goal import CreateGoalUseCase
        uc = CreateGoalUseCase(self._session)
        prediction = await uc._predict(user_id, goal)

        pct = progress["pct_complete"] if progress else 0

        from app.application.goals.notifications import emit_goal_milestone_notifications

        emitted = await emit_goal_milestone_notifications(
            self._session,
            user_id,
            goal_id=goal.id,
            goal_name=goal.name,
            current_amount=float(goal.current_amount),
            target_amount=float(goal.target_amount),
            previous_pct=previous_pct,
            current_pct=pct,
        )

        logger.info("goal_refreshed", user_id=str(user_id), goal_id=str(goal_id), pct=pct, notifications=emitted)

        return {
            "id": str(goal.id), "name": goal.name,
            "target_amount": str(goal.target_amount), "current_amount": str(goal.current_amount),
            "status": goal.status, "progress": progress, "prediction": prediction,
            "milestones_emitted": emitted,
        }
