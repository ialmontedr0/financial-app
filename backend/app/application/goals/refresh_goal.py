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

        goal = await self._repo.recalculate_progress(goal_id, user_id)
        if goal is None:
            raise NotFoundError("Goal")

        progress = await self._repo.get_goal_progress(goal_id, user_id)

        from app.application.goals.create_goal import CreateGoalUseCase
        uc = CreateGoalUseCase(self._session)
        prediction = await uc._predict(user_id, goal)

        pct = progress["pct_complete"] if progress else 0
        for ms in [25, 50, 75, 90, 100]:
            if pct >= ms and goal.milestone_reached_pct < ms:
                event = "goal_completed" if ms == 100 else f"milestone_{ms}"
                await self._repo.create_milestone(
                    user_id, goal_id=goal.id, event_type=event,
                    amount_at_event=goal.current_amount, target_amount=goal.target_amount,
                    pct_complete=pct, notes=f"Milestone {ms}% reached",
                )

        logger.info("goal_refreshed", user_id=str(user_id), goal_id=str(goal_id), pct=pct)

        return {
            "id": str(goal.id), "name": goal.name,
            "target_amount": str(goal.target_amount), "current_amount": str(goal.current_amount),
            "status": goal.status, "progress": progress, "prediction": prediction,
        }
