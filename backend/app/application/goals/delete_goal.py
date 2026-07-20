"""Use case: Delete a financial goal."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.goal_repository import GoalRepository

if TYPE_CHECKING:
    import uuid
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class DeleteGoalUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = GoalRepository(session)

    async def execute(self, user_id: uuid.UUID, goal_id: uuid.UUID) -> dict:
        from app.middleware.error_handler import NotFoundError

        goal = await self._repo.get_goal_by_id(goal_id, user_id)
        if goal is None:
            raise NotFoundError("Goal")

        deleted = await self._repo.delete_goal(goal_id, user_id)
        if not deleted:
            raise NotFoundError("Goal")

        logger.info("goal_deleted", user_id=str(user_id), goal_id=str(goal_id))
        return {"message": "Goal deleted successfully"}
