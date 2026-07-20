"""Use case: Create a what-if simulation for a goal."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.goal_repository import GoalRepository

if TYPE_CHECKING:
    import uuid
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class CreateSimulationUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = GoalRepository(session)

    async def execute(
        self, user_id: uuid.UUID, goal_id: uuid.UUID, *, name: str, monthly_contribution: float,
        lump_sum: float | None = None, lump_sum_date: str | None = None,
        interest_rate: float | None = None, increase_pct: float | None = None, notes: str | None = None,
    ) -> dict:
        from datetime import date as date_type, timedelta

        from app.middleware.error_handler import NotFoundError, ValidationError

        goal = await self._repo.get_goal_by_id(goal_id, user_id)
        if goal is None:
            raise NotFoundError("Goal")
        if not name or not name.strip():
            raise ValidationError("Simulation name es requerido")
        if monthly_contribution <= 0:
            raise ValidationError("monthly_contribution debe ser mayor a 0")

        remaining = float(goal.target_amount) - float(goal.current_amount)
        if remaining <= 0:
            raise ValidationError("Goal ya esta completada")

        monthly = monthly_contribution
        rate = (interest_rate or 0) / 100 / 12
        balance = 0.0
        months = 0
        projection = []
        total_contributions = 0.0
        total_interest = 0.0
        lump_applied = False

        ls_date = None
        if lump_sum_date:
            try:
                ls_date = date_type.fromisoformat(lump_sum_date)
            except ValueError:
                raise ValidationError("lump_sum_date formato invalido (YYYY-MM-DD)")

        current_month = goal.start_date
        while balance < remaining and months < 600:
            months += 1
            contribution = monthly
            if increase_pct and months > 1:
                contribution = monthly * (1 + (float(increase_pct) / 100 * (months - 1)))
            if lump_sum and ls_date and not lump_applied and current_month >= ls_date:
                contribution += lump_sum
                lump_applied = True
            interest = balance * rate
            balance = balance + contribution + interest
            total_contributions += contribution
            total_interest += interest
            current_month = goal.start_date + timedelta(days=months * 30.44)
            projection.append({"month": months, "contribution": round(contribution, 2), "interest": round(interest, 2), "cumulative": round(balance, 2), "date": current_month.isoformat()})

        predicted_date = goal.start_date + timedelta(days=int(months * 30.44))
        if predicted_date > goal.target_date:
            probability = max(0.0, 1.0 - ((predicted_date - goal.target_date).days / 365.0))
        else:
            probability = min(1.0, 1.0 - max((goal.target_date - predicted_date).days / 365.0, 0))

        sim = await self._repo.create_simulation(
            user_id, goal_id=goal.id, name=name.strip(), monthly_contribution=monthly_contribution,
            lump_sum=lump_sum, lump_sum_date=ls_date, interest_rate=interest_rate, increase_pct=increase_pct,
            predicted_completion_date=predicted_date, predicted_probability=round(probability, 4),
            total_contributions=round(total_contributions, 2), total_interest=round(total_interest, 2),
            months_to_complete=months, projection=projection, notes=notes,
        )

        logger.info("simulation_created", user_id=str(user_id), goal_id=str(goal_id), months=months)

        return {
            "id": str(sim.id), "name": sim.name, "goal_id": str(goal.id), "goal_name": goal.name,
            "monthly_contribution": str(sim.monthly_contribution),
            "lump_sum": str(sim.lump_sum) if sim.lump_sum else None,
            "lump_sum_date": sim.lump_sum_date.isoformat() if sim.lump_sum_date else None,
            "interest_rate": str(sim.interest_rate) if sim.interest_rate else None,
            "increase_pct": str(sim.increase_pct) if sim.increase_pct else None,
            "predicted_completion_date": sim.predicted_completion_date.isoformat() if sim.predicted_completion_date else None,
            "predicted_probability": float(sim.predicted_probability) if sim.predicted_probability else None,
            "total_contributions": str(sim.total_contributions), "total_interest": str(sim.total_interest),
            "months_to_complete": sim.months_to_complete, "projection": projection,
            "notes": sim.notes, "created_at": sim.created_at.isoformat() if sim.created_at else None,
        }
