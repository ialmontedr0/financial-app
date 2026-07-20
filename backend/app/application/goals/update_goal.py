"""Use case: Update a financial goal."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.goal_repository import GoalRepository

if TYPE_CHECKING:
    import uuid
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class UpdateGoalUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = GoalRepository(session)

    async def execute(self, user_id: uuid.UUID, goal_id: uuid.UUID, *, changes: dict) -> dict:
        from app.middleware.error_handler import NotFoundError, ValidationError

        goal = await self._repo.get_goal_by_id(goal_id, user_id)
        if goal is None:
            raise NotFoundError("Goal")
        if goal.status == "completed":
            raise ValidationError("Cannot modify a completed goal")

        allowed = {"name", "description", "target_amount", "target_date", "monthly_contribution", "interest_rate", "compound_frequency", "priority", "auto_contribute", "icon", "color", "image_url", "status", "account_id", "category_id"}
        updates = {k: v for k, v in changes.items() if k in allowed}

        if "target_amount" in updates and float(updates["target_amount"]) <= 0:
            raise ValidationError("target_amount debe ser mayor a 0")
        if "priority" in updates and (updates["priority"] < 1 or updates["priority"] > 5):
            raise ValidationError("priority debe ser entre 1 y 5")
        if "status" in updates and updates["status"] not in {"active", "paused", "cancelled"}:
            raise ValidationError(f"status no valido: {updates['status']}")

        updated = await self._repo.update_goal(goal_id, user_id, **updates)
        if updated is None:
            raise NotFoundError("Goal")

        financial_keys = {"target_amount", "monthly_contribution", "interest_rate", "compound_frequency", "target_date"}
        if financial_keys & set(updates.keys()):
            from app.application.goals.create_goal import CreateGoalUseCase
            uc = CreateGoalUseCase(self._session)
            await uc._predict(user_id, updated)

        logger.info("goal_updated", user_id=str(user_id), goal_id=str(goal_id))

        return {
            "id": str(updated.id), "name": updated.name, "description": updated.description,
            "goal_type": updated.goal_type, "target_amount": str(updated.target_amount),
            "current_amount": str(updated.current_amount),
            "start_date": updated.start_date.isoformat(), "target_date": updated.target_date.isoformat(),
            "status": updated.status, "priority": updated.priority,
            "monthly_contribution": str(updated.monthly_contribution) if updated.monthly_contribution else None,
            "auto_contribute": updated.auto_contribute,
            "interest_rate": str(updated.interest_rate) if updated.interest_rate else None,
            "compound_frequency": updated.compound_frequency,
            "account_id": str(updated.account_id) if updated.account_id else None,
            "category_id": str(updated.category_id) if updated.category_id else None,
            "icon": updated.icon, "color": updated.color, "image_url": updated.image_url,
            "predicted_completion_date": updated.predicted_completion_date.isoformat() if updated.predicted_completion_date else None,
            "predicted_probability": float(updated.predicted_probability) if updated.predicted_probability else None,
            "recommended_monthly": str(updated.recommended_monthly) if updated.recommended_monthly else None,
            "updated_at": updated.updated_at.isoformat() if updated.updated_at else None,
        }
