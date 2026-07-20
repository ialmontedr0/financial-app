"""Use case: List simulations for a goal."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.goal_repository import GoalRepository

if TYPE_CHECKING:
    import uuid
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class ListSimulationsUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = GoalRepository(session)

    async def execute(self, user_id: uuid.UUID, goal_id: uuid.UUID) -> dict:
        from app.middleware.error_handler import NotFoundError

        goal = await self._repo.get_goal_by_id(goal_id, user_id)
        if goal is None:
            raise NotFoundError("Goal")

        sims = await self._repo.list_simulations(goal_id, user_id)
        return {
            "goal_id": str(goal.id), "goal_name": goal.name,
            "simulations": [
                {"id": str(s.id), "name": s.name, "monthly_contribution": str(s.monthly_contribution), "lump_sum": str(s.lump_sum) if s.lump_sum else None, "interest_rate": str(s.interest_rate) if s.interest_rate else None, "increase_pct": str(s.increase_pct) if s.increase_pct else None, "predicted_completion_date": s.predicted_completion_date.isoformat() if s.predicted_completion_date else None, "predicted_probability": float(s.predicted_probability) if s.predicted_probability else None, "total_contributions": str(s.total_contributions) if s.total_contributions else None, "months_to_complete": s.months_to_complete, "notes": s.notes, "created_at": s.created_at.isoformat() if s.created_at else None}
                for s in sims
            ],
            "total": len(sims),
        }
