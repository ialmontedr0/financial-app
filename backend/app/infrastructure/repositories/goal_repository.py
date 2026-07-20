"""Repository for financial goal, milestone, and simulation persistence."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog
from sqlalchemy import func, select

from app.infrastructure.models.financial_goal import FinancialGoalModel
from app.infrastructure.models.goal_milestone import GoalMilestoneModel
from app.infrastructure.models.goal_simulation import GoalSimulationModel
from app.infrastructure.models.transaction import TransactionModel

if TYPE_CHECKING:
    import uuid
    from datetime import date
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class GoalRepository:
    """Repository for financial goal operations."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ==================================================================
    # Goal CRUD
    # ==================================================================

    async def create_goal(self, user_id: uuid.UUID, **kwargs: object) -> FinancialGoalModel:
        goal = FinancialGoalModel(user_id=user_id, **kwargs)  # type: ignore[arg-type]
        self._session.add(goal)
        await self._session.flush()
        logger.info("goal_created", user_id=str(user_id), goal_id=str(goal.id), name=goal.name)
        return goal

    async def get_goal_by_id(self, goal_id: uuid.UUID, user_id: uuid.UUID) -> FinancialGoalModel | None:
        stmt = select(FinancialGoalModel).where(
            FinancialGoalModel.id == goal_id,
            FinancialGoalModel.user_id == user_id,
            FinancialGoalModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_goals(
        self,
        user_id: uuid.UUID,
        *,
        goal_type: str | None = None,
        status: str | None = None,
        priority: int | None = None,
    ) -> list[FinancialGoalModel]:
        stmt = select(FinancialGoalModel).where(
            FinancialGoalModel.user_id == user_id,
            FinancialGoalModel.deleted_at.is_(None),
        )
        if goal_type:
            stmt = stmt.where(FinancialGoalModel.goal_type == goal_type)
        if status:
            stmt = stmt.where(FinancialGoalModel.status == status)
        if priority is not None:
            stmt = stmt.where(FinancialGoalModel.priority == priority)
        stmt = stmt.order_by(FinancialGoalModel.priority.asc(), FinancialGoalModel.created_at.desc())
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update_goal(self, goal_id: uuid.UUID, user_id: uuid.UUID, **kwargs: object) -> FinancialGoalModel | None:
        goal = await self.get_goal_by_id(goal_id, user_id)
        if goal is None:
            return None
        for key, value in kwargs.items():
            if hasattr(goal, key):
                setattr(goal, key, value)
        await self._session.flush()
        await self._session.refresh(goal)
        return goal

    async def delete_goal(self, goal_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        from datetime import UTC, datetime

        goal = await self.get_goal_by_id(goal_id, user_id)
        if goal is None:
            return False
        goal.deleted_at = datetime.now(UTC)
        await self._session.flush()
        return True

    # ==================================================================
    # Progress & Recalculation
    # ==================================================================

    async def recalculate_progress(self, goal_id: uuid.UUID, user_id: uuid.UUID) -> FinancialGoalModel | None:
        goal = await self.get_goal_by_id(goal_id, user_id)
        if goal is None:
            return None

        stmt = select(func.coalesce(func.sum(TransactionModel.amount), 0)).where(
            TransactionModel.user_id == user_id,
            TransactionModel.transaction_type == "income",
            TransactionModel.status == "completed",
            TransactionModel.effective_date >= goal.start_date,
            TransactionModel.deleted_at.is_(None),
        )
        if goal.category_id:
            stmt = stmt.where(TransactionModel.category_id == goal.category_id)
        if goal.account_id:
            stmt = stmt.where(TransactionModel.account_id == goal.account_id)

        result = await self._session.execute(stmt)
        total_income = result.scalar_one()
        goal.current_amount = total_income

        target = float(goal.target_amount)
        current = float(goal.current_amount)
        pct = round((current / target * 100), 2) if target > 0 else 0.0
        pct = min(pct, 100.0)

        from datetime import date as date_type

        if pct >= 100.0 and goal.status == "active":
            goal.status = "completed"
            goal.completed_date = date_type.today()
        elif pct >= 90 and goal.milestone_reached_pct < 90:
            goal.milestone_reached_pct = 90
        elif pct >= 75 and goal.milestone_reached_pct < 75:
            goal.milestone_reached_pct = 75
        elif pct >= 50 and goal.milestone_reached_pct < 50:
            goal.milestone_reached_pct = 50
        elif pct >= 25 and goal.milestone_reached_pct < 25:
            goal.milestone_reached_pct = 25

        await self._session.flush()
        await self._session.refresh(goal)
        return goal

    async def get_goal_progress(self, goal_id: uuid.UUID, user_id: uuid.UUID) -> dict | None:
        goal = await self.recalculate_progress(goal_id, user_id)
        if goal is None:
            return None

        target = float(goal.target_amount)
        current = float(goal.current_amount)
        remaining = max(target - current, 0)
        pct = round((current / target * 100), 2) if target > 0 else 0.0

        from datetime import date as date_type

        today = date_type.today()
        days_left = max((goal.target_date - today).days, 0)
        months_left = max(round(days_left / 30.44, 1), 0)
        monthly_needed = round(remaining / months_left, 2) if months_left > 0 else remaining

        days_total = max((goal.target_date - goal.start_date).days, 1)
        days_elapsed = max((today - goal.start_date).days, 0)
        time_pct = round((days_elapsed / days_total * 100), 1)
        behind = pct < time_pct

        return {
            "goal_id": str(goal.id),
            "name": goal.name,
            "target_amount": str(goal.target_amount),
            "current_amount": str(goal.current_amount),
            "remaining": str(round(remaining, 2)),
            "pct_complete": pct,
            "target_date": goal.target_date.isoformat(),
            "days_left": days_left,
            "months_left": months_left,
            "monthly_needed": str(round(monthly_needed, 2)),
            "time_pct": time_pct,
            "behind_schedule": behind,
            "status": goal.status,
            "milestone_reached_pct": goal.milestone_reached_pct,
        }

    # ==================================================================
    # Milestones
    # ==================================================================

    async def create_milestone(self, user_id: uuid.UUID, **kwargs: object) -> GoalMilestoneModel:
        milestone = GoalMilestoneModel(user_id=user_id, **kwargs)  # type: ignore[arg-type]
        self._session.add(milestone)
        await self._session.flush()
        return milestone

    async def list_milestones(self, goal_id: uuid.UUID, user_id: uuid.UUID) -> list[GoalMilestoneModel]:
        stmt = select(GoalMilestoneModel).where(
            GoalMilestoneModel.goal_id == goal_id,
            GoalMilestoneModel.user_id == user_id,
        ).order_by(GoalMilestoneModel.created_at.desc())
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    # ==================================================================
    # Simulations
    # ==================================================================

    async def create_simulation(self, user_id: uuid.UUID, **kwargs: object) -> GoalSimulationModel:
        sim = GoalSimulationModel(user_id=user_id, **kwargs)  # type: ignore[arg-type]
        self._session.add(sim)
        await self._session.flush()
        logger.info("goal_simulation_created", user_id=str(user_id), simulation_id=str(sim.id))
        return sim

    async def list_simulations(self, goal_id: uuid.UUID, user_id: uuid.UUID) -> list[GoalSimulationModel]:
        stmt = select(GoalSimulationModel).where(
            GoalSimulationModel.goal_id == goal_id,
            GoalSimulationModel.user_id == user_id,
        ).order_by(GoalSimulationModel.created_at.desc())
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_simulation_by_id(self, simulation_id: uuid.UUID, user_id: uuid.UUID) -> GoalSimulationModel | None:
        stmt = select(GoalSimulationModel).where(
            GoalSimulationModel.id == simulation_id,
            GoalSimulationModel.user_id == user_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def delete_simulation(self, simulation_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        sim = await self.get_simulation_by_id(simulation_id, user_id)
        if sim is None:
            return False
        await self._session.delete(sim)
        await self._session.flush()
        return True

    # ==================================================================
    # AI Prediction History
    # ==================================================================

    async def get_user_spending_history(self, user_id: uuid.UUID, months: int = 6) -> dict:
        from datetime import date as date_type, timedelta

        today = date_type.today()
        start = today - timedelta(days=months * 30)

        month_expr = func.date_trunc("month", TransactionModel.effective_date).label("month")

        income_stmt = select(month_expr, func.coalesce(func.sum(TransactionModel.amount), 0).label("total")).where(
            TransactionModel.user_id == user_id,
            TransactionModel.transaction_type == "income",
            TransactionModel.status == "completed",
            TransactionModel.effective_date >= start,
            TransactionModel.deleted_at.is_(None),
        ).group_by(month_expr).order_by(month_expr)
        income_result = await self._session.execute(income_stmt)
        income_data = [{"month": str(row[0]), "total": str(row[1])} for row in income_result.all()]

        expense_stmt = select(month_expr, func.coalesce(func.sum(TransactionModel.amount), 0).label("total")).where(
            TransactionModel.user_id == user_id,
            TransactionModel.transaction_type == "expense",
            TransactionModel.status == "completed",
            TransactionModel.effective_date >= start,
            TransactionModel.deleted_at.is_(None),
        ).group_by(month_expr).order_by(month_expr)
        expense_result = await self._session.execute(expense_stmt)
        expense_data = [{"month": str(row[0]), "total": str(row[1])} for row in expense_result.all()]

        total_income = sum(float(d["total"]) for d in income_data)
        total_expense = sum(float(d["total"]) for d in expense_data)
        avg_monthly_savings = (total_income - total_expense) / max(len(income_data), 1)

        return {
            "income": income_data,
            "expenses": expense_data,
            "total_income": total_income,
            "total_expenses": total_expense,
            "avg_monthly_savings": round(avg_monthly_savings, 2),
            "months_analyzed": max(len(income_data), 1),
        }

    # ==================================================================
    # Summary
    # ==================================================================

    async def get_goals_summary(self, user_id: uuid.UUID) -> dict:
        goals = await self.list_goals(user_id)
        active = [g for g in goals if g.status == "active"]
        completed = [g for g in goals if g.status == "completed"]

        total_target_active = sum(float(g.target_amount) for g in active)
        total_current = sum(float(g.current_amount) for g in active)
        pct_overall = round((total_current / total_target_active * 100), 1) if total_target_active > 0 else 0.0

        behind_count = 0
        for g in active:
            from datetime import date as date_type

            today = date_type.today()
            days_total = max((g.target_date - g.start_date).days, 1)
            days_elapsed = max((today - g.start_date).days, 0)
            time_pct = days_elapsed / days_total * 100
            current_pct = float(g.current_amount) / float(g.target_amount) * 100 if float(g.target_amount) > 0 else 0
            if current_pct < time_pct:
                behind_count += 1

        return {
            "total_goals": len(goals),
            "active_goals": len(active),
            "completed_goals": len(completed),
            "total_target_amount": str(round(sum(float(g.target_amount) for g in goals), 2)),
            "total_current_amount": str(round(total_current, 2)),
            "overall_progress_pct": pct_overall,
            "behind_schedule_count": behind_count,
            "on_track_count": len(active) - behind_count,
        }
