"""Use case: Refresh AI prediction for a goal."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.goal_repository import GoalRepository

if TYPE_CHECKING:
    import uuid
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class RefreshPredictionUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = GoalRepository(session)

    async def execute(self, user_id: uuid.UUID, goal_id: uuid.UUID) -> dict:
        from datetime import UTC, datetime

        from app.middleware.error_handler import NotFoundError

        goal = await self._repo.get_goal_by_id(goal_id, user_id)
        if goal is None:
            raise NotFoundError("Goal")

        from app.application.goals.create_goal import CreateGoalUseCase
        uc = CreateGoalUseCase(self._session)
        prediction = await uc._predict(user_id, goal)

        await self._repo.update_goal(goal_id, user_id, prediction_updated_at=datetime.now(UTC))

        await self._repo.create_milestone(
            user_id, goal_id=goal.id, event_type="prediction_update",
            amount_at_event=goal.current_amount, target_amount=goal.target_amount,
            pct_complete=round(float(goal.current_amount) / float(goal.target_amount) * 100, 2) if float(goal.target_amount) > 0 else 0,
            metadata_json=prediction,
        )

        logger.info("prediction_refreshed", user_id=str(user_id), goal_id=str(goal_id), probability=prediction.get("predicted_probability"))
        return {"goal_id": str(goal.id), "name": goal.name, "prediction": prediction}
