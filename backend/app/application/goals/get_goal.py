"""Use case: Get a single financial goal with progress."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.goal_repository import GoalRepository

if TYPE_CHECKING:
    import uuid
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class GetGoalUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = GoalRepository(session)

    async def execute(self, user_id: uuid.UUID, goal_id: uuid.UUID) -> dict:
        from app.middleware.error_handler import NotFoundError

        goal = await self._repo.get_goal_by_id(goal_id, user_id)
        if goal is None:
            raise NotFoundError("Goal")

        progress = await self._repo.get_goal_progress(goal_id, user_id)
        milestones = await self._repo.list_milestones(goal_id, user_id)

        return {
            "id": str(goal.id), "name": goal.name, "description": goal.description,
            "goal_type": goal.goal_type, "target_amount": str(goal.target_amount),
            "current_amount": str(goal.current_amount),
            "start_date": goal.start_date.isoformat(), "target_date": goal.target_date.isoformat(),
            "completed_date": goal.completed_date.isoformat() if goal.completed_date else None,
            "status": goal.status, "priority": goal.priority,
            "monthly_contribution": str(goal.monthly_contribution) if goal.monthly_contribution else None,
            "auto_contribute": goal.auto_contribute,
            "interest_rate": str(goal.interest_rate) if goal.interest_rate else None,
            "compound_frequency": goal.compound_frequency,
            "account_id": str(goal.account_id) if goal.account_id else None,
            "category_id": str(goal.category_id) if goal.category_id else None,
            "icon": goal.icon, "color": goal.color, "image_url": goal.image_url,
            "milestone_reached_pct": goal.milestone_reached_pct,
            "progress": progress,
            "milestones": [
                {"id": str(m.id), "event_type": m.event_type, "amount_at_event": str(m.amount_at_event), "pct_complete": str(m.pct_complete), "contribution_amount": str(m.contribution_amount) if m.contribution_amount else None, "notes": m.notes, "created_at": m.created_at.isoformat() if m.created_at else None}
                for m in milestones
            ],
            "prediction": {
                "predicted_completion_date": goal.predicted_completion_date.isoformat() if goal.predicted_completion_date else None,
                "predicted_probability": float(goal.predicted_probability) if goal.predicted_probability else None,
                "recommended_monthly": str(goal.recommended_monthly) if goal.recommended_monthly else None,
                "prediction_updated_at": goal.prediction_updated_at.isoformat() if goal.prediction_updated_at else None,
            },
            "created_at": goal.created_at.isoformat() if goal.created_at else None,
            "updated_at": goal.updated_at.isoformat() if goal.updated_at else None,
        }
