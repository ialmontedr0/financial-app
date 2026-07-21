"""Savings optimizer — generates actionable savings recommendations."""

from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal
from statistics import mean
from typing import Any

import structlog
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.models.financial_goal import FinancialGoalModel
from app.infrastructure.models.loan import LoanModel
from app.infrastructure.models.transaction import TransactionModel

logger = structlog.get_logger()

# 50/30/20 rule targets
NEEDS_TARGET = 0.50
WANTS_TARGET = 0.30
SAVINGS_TARGET = 0.20


class SavingsOptimizer:
    """Generates savings optimization recommendations."""

    async def optimize(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
    ) -> dict[str, Any]:
        """Run full savings optimization.

        Returns:
        - allocation_50_30_20: actual vs recommended
        - goal_allocation: optimal goal contributions
        - debt_strategy: snowball vs avalanche recommendation
        - seasonal_opportunities: months with potential savings
        - estimated_total_savings: total potential monthly savings
        - recommendations: actionable savings recommendations
        """
        today = date.today()
        six_months_ago = today - timedelta(days=180)

        allocation = await self._analyze_50_30_20(session, user_id, six_months_ago, today)
        goal_alloc = await self._optimize_goal_allocation(session, user_id)
        debt_strategy = await self._recommend_debt_strategy(session, user_id)
        seasonal = await self._find_seasonal_opportunities(session, user_id, six_months_ago, today)
        recs = self._generate_savings_recommendations(
            allocation, goal_alloc, debt_strategy, seasonal
        )

        total_savings = sum(r.get("estimated_savings", 0) for r in recs)

        return {
            "allocation_50_30_20": allocation,
            "goal_allocation": goal_alloc,
            "debt_strategy": debt_strategy,
            "seasonal_opportunities": seasonal,
            "estimated_total_savings": round(total_savings, 2),
            "recommendations": recs,
        }

    async def simulate(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
        monthly_amount: float,
        months: int = 12,
        annual_return_pct: float = 0.0,
    ) -> dict[str, Any]:
        """Simulate savings accumulation over time."""
        monthly_rate = annual_return_pct / 100 / 12
        projections: list[dict[str, Any]] = []
        balance = 0.0

        for m in range(1, months + 1):
            balance = balance * (1 + monthly_rate) + monthly_amount
            projections.append(
                {
                    "month": m,
                    "contribution": monthly_amount,
                    "interest": round(
                        balance - (monthly_amount * m) - (balance * monthly_rate if m > 1 else 0), 2
                    ),
                    "balance": round(balance, 2),
                }
            )

        return {
            "monthly_amount": monthly_amount,
            "months": months,
            "annual_return_pct": annual_return_pct,
            "final_balance": round(balance, 2),
            "total_contributed": round(monthly_amount * months, 2),
            "total_interest": round(balance - monthly_amount * months, 2),
            "projections": projections,
        }

    # ---- Private helpers ----

    async def _analyze_50_30_20(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
        start: date,
        end: date,
    ) -> dict[str, Any]:
        """Analyze actual allocation vs 50/30/20 rule."""
        # Total income
        income_stmt = select(func.coalesce(func.sum(TransactionModel.amount), 0)).where(
            and_(
                TransactionModel.user_id == user_id,
                TransactionModel.deleted_at.is_(None),
                TransactionModel.transaction_type == "income",
                TransactionModel.status == "completed",
                TransactionModel.effective_date >= start,
                TransactionModel.effective_date <= end,
            )
        )
        total_income = float((await session.execute(income_stmt)).scalar() or 0)

        # Total expenses (need to classify into needs/wants/savings)
        expense_stmt = select(TransactionModel).where(
            and_(
                TransactionModel.user_id == user_id,
                TransactionModel.deleted_at.is_(None),
                TransactionModel.transaction_type == "expense",
                TransactionModel.status == "completed",
                TransactionModel.effective_date >= start,
                TransactionModel.effective_date <= end,
            )
        )
        result = await session.execute(expense_stmt)
        expenses = list(result.scalars().all())

        # Simple classification heuristic based on category keywords
        needs_keywords = {
            "rent",
            "alquiler",
            "utilities",
            "servicios",
            "food",
            "alimentacion",
            "supermercado",
            "transporte",
            "transport",
            "salud",
            "health",
            "insurance",
            "seguro",
            "education",
            "educacion",
            "debt",
            "deuda",
            "loan",
            "prestamo",
        }
        wants_keywords = {
            "entertainment",
            "entretenimiento",
            "restaurant",
            "restaurante",
            "travel",
            "viaje",
            "shopping",
            "compras",
            "gym",
            "subscription",
            "suscripcion",
            "streaming",
            "luxury",
            "lujo",
            "coffee",
            "cafe",
        }

        needs_total = 0.0
        wants_total = 0.0
        for t in expenses:
            amount = float(t.amount)
            cat_name = (t.description or "").lower()
            # Simple heuristic: check category_id name or description
            is_need = any(kw in cat_name for kw in needs_keywords)
            is_want = any(kw in cat_name for kw in wants_keywords)

            if is_need and not is_want:
                needs_total += amount
            elif is_want and not is_need:
                wants_total += amount
            else:
                # Default: split 60/40 needs/wants
                needs_total += amount * 0.6
                wants_total += amount * 0.4

        total_expenses = needs_total + wants_total
        actual_savings = total_income - total_expenses

        # Actual percentages
        actual_needs_pct = needs_total / total_income if total_income > 0 else 0
        actual_wants_pct = wants_total / total_income if total_income > 0 else 0
        actual_savings_pct = actual_savings / total_income if total_income > 0 else 0

        return {
            "total_income": round(total_income, 2),
            "total_expenses": round(total_expenses, 2),
            "actual_savings": round(actual_savings, 2),
            "actual": {
                "needs_pct": round(actual_needs_pct * 100, 1),
                "wants_pct": round(actual_wants_pct * 100, 1),
                "savings_pct": round(actual_savings_pct * 100, 1),
            },
            "recommended": {
                "needs_pct": NEEDS_TARGET * 100,
                "wants_pct": WANTS_TARGET * 100,
                "savings_pct": SAVINGS_TARGET * 100,
            },
            "deviation": {
                "needs_diff": round((actual_needs_pct - NEEDS_TARGET) * 100, 1),
                "wants_diff": round((actual_wants_pct - WANTS_TARGET) * 100, 1),
                "savings_diff": round((actual_savings_pct - SAVINGS_TARGET) * 100, 1),
            },
        }

    async def _optimize_goal_allocation(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
    ) -> dict[str, Any]:
        """Optimize savings allocation across active goals."""
        stmt = (
            select(FinancialGoalModel)
            .where(
                and_(
                    FinancialGoalModel.user_id == user_id,
                    FinancialGoalModel.status == "active",
                    FinancialGoalModel.deleted_at.is_(None),
                )
            )
            .order_by(FinancialGoalModel.priority)
        )
        result = await session.execute(stmt)
        goals = list(result.scalars().all())

        if not goals:
            return {"goals": [], "total_recommended": 0, "strategy": "no_active_goals"}

        allocations: list[dict[str, Any]] = []
        total_recommended = 0.0

        for goal in goals:
            target = float(goal.target_amount)
            current = float(goal.current_amount)
            remaining = target - current

            # Priority weight: priority 1 = highest
            priority_weight = 1.0 / max(1, goal.priority)

            # Calculate recommended monthly contribution
            if goal.target_date and goal.start_date:
                months_left = max(1, (goal.target_date - date.today()).days / 30)
                if remaining > 0:
                    monthly_needed = remaining / months_left
                else:
                    monthly_needed = 0
            else:
                monthly_needed = remaining / 12  # default: 12 months

            allocations.append(
                {
                    "goal_id": str(goal.id),
                    "goal_name": goal.name,
                    "goal_type": goal.goal_type,
                    "target_amount": round(target, 2),
                    "current_amount": round(current, 2),
                    "remaining": round(remaining, 2),
                    "progress_pct": round((current / target * 100) if target > 0 else 0, 1),
                    "priority": goal.priority,
                    "priority_weight": round(priority_weight, 3),
                    "recommended_monthly": round(monthly_needed, 2),
                    "target_date": goal.target_date.isoformat() if goal.target_date else None,
                }
            )
            total_recommended += monthly_needed

        # Normalize by total available for savings (use 20% of income as estimate)
        return {
            "goals": allocations,
            "total_recommended_monthly": round(total_recommended, 2),
            "strategy": "priority_weighted",
        }

    async def _recommend_debt_strategy(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
    ) -> dict[str, Any]:
        """Recommend debt payoff strategy: snowball vs avalanche."""
        stmt = select(LoanModel).where(
            and_(
                LoanModel.user_id == user_id,
                LoanModel.status == "active",
                LoanModel.deleted_at.is_(None),
            )
        )
        result = await session.execute(stmt)
        loans = list(result.scalars().all())

        if not loans:
            return {"strategy": "no_debts", "loans": []}

        loan_data = []
        for loan in loans:
            balance = float(loan.balance or loan.principal_amount or 0)
            rate = float(loan.interest_rate or 0)
            payment = float(loan.monthly_payment or 0)
            loan_data.append(
                {
                    "loan_id": str(loan.id),
                    "name": loan.name or "Prestamo",
                    "balance": round(balance, 2),
                    "interest_rate": round(rate, 4),
                    "monthly_payment": round(payment, 2),
                }
            )

        # Snowball: sort by balance ascending (smallest first)
        snowball_order = sorted(loan_data, key=lambda x: x["balance"])

        # Avalanche: sort by interest rate descending (highest first)
        avalanche_order = sorted(loan_data, key=lambda x: x["interest_rate"], reverse=True)

        # Compare total interest paid
        snowball_total = self._simulate_debt_payoff(snowball_order)
        avalanche_total = self._simulate_debt_payoff(avalanche_order)

        savings = snowball_total - avalanche_total

        recommended = "avalanche" if savings > 100 else "snowball"

        return {
            "strategy": recommended,
            "snowball_order": [l["loan_id"] for l in snowball_order],
            "avalanche_order": [l["loan_id"] for l in avalanche_order],
            "estimated_savings_avalanche_vs_snowball": round(savings, 2),
            "loans": loan_data,
        }

    def _simulate_debt_payoff(self, ordered_loans: list[dict[str, Any]]) -> float:
        """Simulate total interest paid with a given payoff order."""
        total_interest = 0.0
        for loan in ordered_loans:
            balance = loan["balance"]
            rate = loan["interest_rate"] / 100 / 12
            payment = loan["monthly_payment"]
            if payment <= 0 or balance <= 0:
                continue
            months = 0
            while balance > 0 and months < 360:
                interest = balance * rate
                total_interest += interest
                principal = min(payment - interest, balance)
                balance -= principal
                months += 1
        return round(total_interest, 2)

    async def _find_seasonal_opportunities(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
        start: date,
        end: date,
    ) -> dict[str, Any]:
        """Find months with historically lower spending."""
        month_trunc = func.date_trunc("month", TransactionModel.effective_date)
        stmt = (
            select(
                func.extract("month", TransactionModel.effective_date).label("month_num"),
                func.sum(TransactionModel.amount).label("total"),
            )
            .where(
                and_(
                    TransactionModel.user_id == user_id,
                    TransactionModel.deleted_at.is_(None),
                    TransactionModel.transaction_type == "expense",
                    TransactionModel.status == "completed",
                    TransactionModel.effective_date >= start,
                    TransactionModel.effective_date <= end,
                )
            )
            .group_by(func.extract("month", TransactionModel.effective_date))
            .order_by(func.extract("month", TransactionModel.effective_date))
        )
        result = await session.execute(stmt)
        rows = result.all()

        monthly_totals = {int(r.month_num): float(r.total) for r in rows}
        if not monthly_totals:
            return {"months": {}, "best_months": [], "worst_months": []}

        avg = mean(monthly_totals.values())

        months_data = {}
        for m, total in monthly_totals.items():
            diff = total - avg
            months_data[m] = {
                "total": round(total, 2),
                "vs_average": round(diff, 2),
                "vs_average_pct": round((diff / avg * 100) if avg > 0 else 0, 1),
                "is_cheaper": diff < 0,
            }

        best = sorted(months_data.keys(), key=lambda m: months_data[m]["total"])[:3]
        worst = sorted(months_data.keys(), key=lambda m: months_data[m]["total"], reverse=True)[:3]

        return {
            "months": months_data,
            "best_months": best,
            "worst_months": worst,
            "average_monthly": round(avg, 2),
        }

    def _generate_savings_recommendations(
        self,
        allocation: dict[str, Any],
        goal_alloc: dict[str, Any],
        debt_strategy: dict[str, Any],
        seasonal: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Generate savings recommendations."""
        recs: list[dict[str, Any]] = []

        # 50/30/20 deviations
        dev = allocation.get("deviation", {})
        if dev.get("savings_diff", 0) < -5:
            gap_pct = abs(dev["savings_diff"])
            income = allocation.get("total_income", 0)
            monthly_gap = income * (gap_pct / 100) / 12  # monthly
            recs.append(
                {
                    "type": "increase_savings",
                    "title": f"Ahorra un {gap_pct:.0f}% mas de tu ingreso",
                    "description": (
                        f"Tu ahorro actual es {allocation['actual']['savings_pct']:.1f}% "
                        f"vs el recomendado del 20%. "
                        f"Necesitas ahorrar ~{monthly_gap:.0f} mas por mes."
                    ),
                    "priority": "high",
                    "estimated_savings": round(monthly_gap, 2),
                    "confidence": 0.85,
                    "category": "50_30_20",
                }
            )

        if dev.get("wants_diff", 0) > 5:
            excess_pct = dev["wants_diff"]
            income = allocation.get("total_income", 0)
            monthly_excess = income * (excess_pct / 100) / 12
            recs.append(
                {
                    "type": "reduce_spending",
                    "title": f"Reduce gastos discrecionales en {excess_pct:.0f}%",
                    "description": (
                        f"Tus gastos de 'deseos' son {allocation['actual']['wants_pct']:.1f}% "
                        f"vs el recomendado del 30%. "
                        f"Considera reducir ~{monthly_excess:.0f}/mes."
                    ),
                    "priority": "medium",
                    "estimated_savings": round(monthly_excess, 2),
                    "confidence": 0.7,
                    "category": "50_30_20",
                }
            )

        # Debt strategy
        if debt_strategy.get("strategy") in ("snowball", "avalanche"):
            savings = debt_strategy.get("estimated_savings_avalanche_vs_snowball", 0)
            if savings > 0:
                strategy_name = (
                    "Avalancha" if debt_strategy["strategy"] == "avalanche" else "Bola de nieve"
                )
                recs.append(
                    {
                        "type": "debt_strategy",
                        "title": f"Usa estrategia {strategy_name}",
                        "description": (
                            f"Con la estrategia {strategy_name.lower()}, "
                            f"podrias ahorrar {savings:.0f} en intereses totales."
                        ),
                        "priority": "medium",
                        "estimated_savings": round(savings / 12, 2),  # monthly equivalent
                        "confidence": 0.75,
                        "category": "debt_strategy",
                    }
                )

        # Goal recommendations
        goals = goal_alloc.get("goals", [])
        total_recommended = goal_alloc.get("total_recommended_monthly", 0)
        if total_recommended > 0:
            recs.append(
                {
                    "type": "savings_allocation",
                    "title": f"Invierte {total_recommended:.0f}/mes en tus metas",
                    "description": (
                        f"Tienes {len(goals)} metas activas. "
                        f"La contribucion mensual recomendada total es {total_recommended:.0f}. "
                        f"Prioriza por orden de prioridad."
                    ),
                    "priority": "medium",
                    "estimated_savings": 0,
                    "confidence": 0.8,
                    "category": "goal_allocation",
                    "details": goals,
                }
            )

        return recs
