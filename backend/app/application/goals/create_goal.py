"""Use case: Create a financial goal."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.goal_repository import GoalRepository

if TYPE_CHECKING:
    import uuid
    from datetime import date
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class CreateGoalUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = GoalRepository(session)

    async def execute(
        self,
        user_id: uuid.UUID,
        *,
        name: str,
        target_amount: float,
        goal_type: str = "savings",
        start_date: date | None = None,
        target_date: date | None = None,
        monthly_contribution: float | None = None,
        interest_rate: float | None = None,
        compound_frequency: str | None = None,
        account_id: uuid.UUID | None = None,
        category_id: uuid.UUID | None = None,
        priority: int = 1,
        auto_contribute: bool = False,
        description: str | None = None,
        icon: str | None = None,
        color: str | None = None,
        image_url: str | None = None,
    ) -> dict:
        from datetime import date as date_type, timedelta

        from app.middleware.error_handler import ValidationError

        if not name or not name.strip():
            raise ValidationError("Goal name es requerido")
        if target_amount <= 0:
            raise ValidationError("target_amount debe ser mayor a 0")

        valid_types = {"savings", "debt_payoff", "investment", "emergency_fund", "purchase", "education", "travel", "custom"}
        if goal_type not in valid_types:
            raise ValidationError(f"goal_type no valido: {goal_type}. Soportado: {', '.join(sorted(valid_types))}")

        if not start_date:
            start_date = date_type.today()
        if not target_date:
            target_date = start_date + timedelta(days=365)
        if target_date <= start_date:
            raise ValidationError("target_date debe ser posterior a start_date")
        if priority < 1 or priority > 5:
            raise ValidationError("priority debe ser entre 1 y 5")

        valid_compound = {None, "monthly", "quarterly", "annually"}
        if compound_frequency not in valid_compound:
            raise ValidationError(f"compound_frequency no valido: {compound_frequency}")
        if interest_rate is not None and interest_rate < 0:
            raise ValidationError("interest_rate no puede ser negativo")

        goal = await self._repo.create_goal(
            user_id,
            name=name.strip(),
            description=description,
            goal_type=goal_type,
            target_amount=target_amount,
            current_amount=0,
            start_date=start_date,
            target_date=target_date,
            status="active",
            priority=priority,
            monthly_contribution=monthly_contribution,
            auto_contribute=auto_contribute,
            interest_rate=interest_rate,
            compound_frequency=compound_frequency,
            account_id=account_id,
            category_id=category_id,
            icon=icon,
            color=color,
            image_url=image_url,
            milestone_reached_pct=0,
        )

        prediction = await self._predict(user_id, goal)

        await self._repo.create_milestone(
            user_id,
            goal_id=goal.id,
            event_type="goal_created",
            amount_at_event=0,
            target_amount=goal.target_amount,
            pct_complete=0,
            notes=f"Goal '{goal.name}' created",
        )

        return {
            "id": str(goal.id),
            "name": goal.name,
            "description": goal.description,
            "goal_type": goal.goal_type,
            "target_amount": str(goal.target_amount),
            "current_amount": str(goal.current_amount),
            "start_date": goal.start_date.isoformat(),
            "target_date": goal.target_date.isoformat(),
            "status": goal.status,
            "priority": goal.priority,
            "monthly_contribution": str(goal.monthly_contribution) if goal.monthly_contribution else None,
            "auto_contribute": goal.auto_contribute,
            "interest_rate": str(goal.interest_rate) if goal.interest_rate else None,
            "compound_frequency": goal.compound_frequency,
            "account_id": str(goal.account_id) if goal.account_id else None,
            "category_id": str(goal.category_id) if goal.category_id else None,
            "icon": goal.icon,
            "color": goal.color,
            "image_url": goal.image_url,
            "prediction": prediction,
            "created_at": goal.created_at.isoformat() if goal.created_at else None,
        }

    async def _predict(self, user_id: uuid.UUID, goal: object) -> dict:
        history = await self._repo.get_user_spending_history(user_id)
        remaining = float(goal.target_amount) - float(goal.current_amount)
        if remaining <= 0:
            return {"predicted_completion_date": None, "predicted_probability": 1.0, "recommended_monthly": "0", "message": "Goal already reached"}

        monthly = float(goal.monthly_contribution) if goal.monthly_contribution else history["avg_monthly_savings"]
        if monthly <= 0:
            return {"predicted_completion_date": None, "predicted_probability": 0.0, "recommended_monthly": str(round(remaining / 12, 2)), "message": "No savings capacity detected"}

        if goal.interest_rate and float(goal.interest_rate) > 0:
            months = self._calc_compound_months(remaining, monthly, float(goal.interest_rate), goal.compound_frequency or "monthly")
        else:
            months = max(int(remaining / monthly), 1)

        from datetime import date as date_type, timedelta

        predicted_date = goal.start_date + timedelta(days=int(months * 30.44))
        if predicted_date > goal.target_date:
            probability = max(0.0, 1.0 - ((predicted_date - goal.target_date).days / 365.0))
        else:
            probability = min(1.0, 1.0 - max((goal.target_date - predicted_date).days / 365.0, 0))

        if history["avg_monthly_savings"] > 0 and monthly <= history["avg_monthly_savings"]:
            probability = min(probability * 1.1, 1.0)

        recommended = remaining / max((goal.target_date - goal.start_date).days / 30.44, 1)

        await self._repo.update_goal(
            goal.id, user_id,
            predicted_completion_date=predicted_date,
            predicted_probability=round(probability, 4),
            recommended_monthly=round(recommended, 2),
        )

        return {
            "predicted_completion_date": predicted_date.isoformat(),
            "predicted_probability": round(probability, 4),
            "recommended_monthly": str(round(recommended, 2)),
            "months_to_complete": months,
            "features_used": {"avg_monthly_savings": history["avg_monthly_savings"], "months_analyzed": history["months_analyzed"], "monthly_contribution": monthly, "interest_rate": str(goal.interest_rate) if goal.interest_rate else None},
            "model_version": "goal_predictor_v1.0",
        }

    @staticmethod
    def _calc_compound_months(principal: float, monthly: float, annual_rate: float, freq: str) -> int:
        monthly_rate = annual_rate / 100 / 12
        months = 0
        balance = 0.0
        while balance < principal and months < 600:
            months += 1
            if freq == "quarterly":
                balance = balance + monthly
                if months % 3 == 0:
                    balance = balance * (1 + annual_rate / 100 / 4)
            else:
                balance = (balance + monthly) * (1 + monthly_rate)
        return months
