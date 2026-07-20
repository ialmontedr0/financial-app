"""Use case: List financial goals."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.goal_repository import GoalRepository

if TYPE_CHECKING:
    import uuid
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class ListGoalsUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = GoalRepository(session)

    async def execute(self, user_id: uuid.UUID, *, goal_type: str | None = None, status: str | None = None, priority: int | None = None) -> dict:
        goals = await self._repo.list_goals(user_id, goal_type=goal_type, status=status, priority=priority)
        result = []
        for g in goals:
            target = float(g.target_amount)
            current = float(g.current_amount)
            pct = round((current / target * 100), 2) if target > 0 else 0.0
            result.append({
                "id": str(g.id), "name": g.name, "description": g.description, "goal_type": g.goal_type,
                "target_amount": str(g.target_amount), "current_amount": str(g.current_amount), "pct_complete": pct,
                "start_date": g.start_date.isoformat(), "target_date": g.target_date.isoformat(),
                "status": g.status, "priority": g.priority,
                "monthly_contribution": str(g.monthly_contribution) if g.monthly_contribution else None,
                "interest_rate": str(g.interest_rate) if g.interest_rate else None,
                "predicted_completion_date": g.predicted_completion_date.isoformat() if g.predicted_completion_date else None,
                "predicted_probability": float(g.predicted_probability) if g.predicted_probability else None,
                "recommended_monthly": str(g.recommended_monthly) if g.recommended_monthly else None,
                "icon": g.icon, "color": g.color, "image_url": g.image_url,
                "milestone_reached_pct": g.milestone_reached_pct,
                "created_at": g.created_at.isoformat() if g.created_at else None,
            })
        return {"goals": result, "total": len(result)}
