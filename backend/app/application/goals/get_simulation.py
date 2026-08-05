"""Use case: Get a single simulation with full details."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.goal_repository import GoalRepository

if TYPE_CHECKING:
    import uuid
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class GetSimulationUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = GoalRepository(session)

    async def execute(
        self, user_id: uuid.UUID, goal_id: uuid.UUID, simulation_id: uuid.UUID
    ) -> dict:
        from app.middleware.error_handler import NotFoundError

        goal = await self._repo.get_goal_by_id(goal_id, user_id)
        if goal is None:
            raise NotFoundError("Goal")

        sim = await self._repo.get_simulation_by_id(simulation_id, user_id)
        if sim is None:
            raise NotFoundError("Simulation")

        months = sim.months_to_complete
        proj = sim.projection or {}
        if isinstance(proj, dict) and "months" in proj:
            months_data = proj["months"]
            params = proj.get("params", {})
            mc_data = proj.get("monte_carlo")
            recommendations = proj.get("recommendations")
            total_income_used = proj.get("total_income_used")
        else:
            months_data = proj if isinstance(proj, list) else []
            params = {}
            mc_data = None
            recommendations = None
            total_income_used = None

        return {
            "id": str(sim.id),
            "name": sim.name,
            "goal_id": str(goal.id),
            "goal_name": goal.name,
            "goal_target_amount": str(goal.target_amount),
            "goal_current_amount": str(goal.current_amount),
            "starting_amount": str(goal.current_amount),
            "monthly_contribution": str(sim.monthly_contribution),
            "lump_sum": str(sim.lump_sum) if sim.lump_sum else None,
            "lump_sum_date": sim.lump_sum_date.isoformat() if sim.lump_sum_date else None,
            "interest_rate": str(sim.interest_rate) if sim.interest_rate else None,
            "increase_pct": str(sim.increase_pct) if sim.increase_pct else None,
            "inflation_rate": str(params.get("inflation_rate"))
            if params.get("inflation_rate")
            else None,
            "income_sources": params.get("income_sources", []),
            "expenses": params.get("expenses", []),
            "predicted_completion_date": sim.predicted_completion_date.isoformat()
            if sim.predicted_completion_date
            else None,
            "predicted_probability": float(sim.predicted_probability)
            if sim.predicted_probability
            else None,
            "total_contributions": str(sim.total_contributions)
            if sim.total_contributions
            else None,
            "total_interest": str(sim.total_interest) if sim.total_interest else None,
            "total_income_used": str(total_income_used) if total_income_used else None,
            "months_to_complete": months,
            "projection": months_data,
            "monte_carlo": mc_data,
            "recommendations": recommendations,
            "notes": sim.notes,
            "created_at": sim.created_at.isoformat() if sim.created_at else None,
        }
