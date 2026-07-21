"""Financial recommendation engine.

Combines rule-based heuristics with ML insights to generate
personalized financial recommendations.

No ML dependency - uses statistical analysis of user data.
"""

from __future__ import annotations

import uuid
from datetime import date, timedelta

import structlog
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.models.budget import BudgetModel
from app.infrastructure.models.financial_account import FinancialAccountModel
from app.infrastructure.models.subscription import SubscriptionModel
from app.infrastructure.models.transaction import TransactionModel

logger = structlog.get_logger()


class RecommendationEngine:
    """Generates personalized financial recommendations."""

    async def generate(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
    ) -> list[dict]:
        """Generate all recommendations for a user.

        Returns a list of recommendation dicts, each with:
        - type: str
        - title: str
        - description: str
        - priority: str (high, medium, low)
        - estimated_savings: float
        - confidence: float
        - features_used: dict
        """
        recommendations: list[dict] = []

        recommendations.extend(await self._check_spending_spikes(session, user_id))
        recommendations.extend(await self._check_subscription_optimization(session, user_id))
        recommendations.extend(await self._check_savings_rate(session, user_id))
        recommendations.extend(await self._check_budget_utilization(session, user_id))
        recommendations.extend(await self._check_emergency_fund(session, user_id))
        recommendations.extend(await self._check_category_spending(session, user_id))

        priority_order = {"high": 0, "medium": 1, "low": 2}
        recommendations.sort(
            key=lambda r: (priority_order.get(r["priority"], 3), -r.get("estimated_savings", 0))
        )

        return recommendations

    # ==============================================================
    # 1. Spending Spikes
    # ==============================================================

    async def _check_spending_spikes(self, session: AsyncSession, user_id: uuid.UUID) -> list[dict]:
        """Detect spending spikes compared to 3-month average."""
        recs: list[dict] = []
        today = date.today()
        current_month_start = today.replace(day=1)
        three_months_ago = (today - timedelta(days=90)).replace(day=1)

        current_stmt = select(func.coalesce(func.sum(TransactionModel.amount), 0)).where(
            and_(
                TransactionModel.user_id == user_id,
                TransactionModel.deleted_at.is_(None),
                TransactionModel.transaction_type == "expense",
                TransactionModel.status == "completed",
                TransactionModel.effective_date >= current_month_start,
            )
        )
        current_total = float((await session.execute(current_stmt)).scalar() or 0)

        # Average of previous 3 months
        month_trunc = func.date_trunc("month", TransactionModel.effective_date)
        monthly_subq = (
            select(
                month_trunc.label("month"),
                func.sum(TransactionModel.amount).label("total"),
            )
            .where(
                and_(
                    TransactionModel.user_id == user_id,
                    TransactionModel.deleted_at.is_(None),
                    TransactionModel.transaction_type == "expense",
                    TransactionModel.status == "completed",
                    TransactionModel.effective_date >= three_months_ago,
                    TransactionModel.effective_date < current_month_start,
                )
            )
            .group_by(month_trunc)
            .subquery()
        )
        avg_stmt = select(func.avg(monthly_subq.c.total))
        avg_monthly = float((await session.execute(avg_stmt)).scalar() or 0)

        if avg_monthly > 0 and current_total > avg_monthly * 1.2:
            spike_pct = ((current_total - avg_monthly) / avg_monthly) * 100
            recs.append(
                {
                    "type": "reduce_spending",
                    "title": f"Gasto elevado este mes (+{spike_pct:.0f}%)",
                    "description": (
                        f"Tu gasto actual ({current_total:.0f}) esta un {spike_pct:.0f}% "
                        f"por encima de tu promedio mensual ({avg_monthly:.0f}). "
                        f"Revisa tus categorias de gasto para identificar incrementos inusuales."
                    ),
                    "priority": "high" if spike_pct > 50 else "medium",
                    "estimated_savings": round(current_total - avg_monthly, 2),
                    "confidence": 0.8,
                    "features_used": {
                        "current_month": current_total,
                        "avg_monthly": round(avg_monthly, 2),
                        "spike_percentage": round(spike_pct, 2),
                    },
                }
            )

        return recs

    # ==============================================================
    # 2. Subscription Optimization
    # ==============================================================

    async def _check_subscription_optimization(
        self, session: AsyncSession, user_id: uuid.UUID
    ) -> list[dict]:
        """Identify costly subscriptions that could be optimized."""
        recs: list[dict] = []

        stmt = select(SubscriptionModel).where(
            and_(
                SubscriptionModel.user_id == user_id,
                SubscriptionModel.status == "active",
                SubscriptionModel.deleted_at.is_(None),
            )
        )
        result = await session.execute(stmt)
        subscriptions = list(result.scalars().all())

        total_monthly = 0.0
        for sub in subscriptions:
            monthly = float(sub.amount)
            if sub.billing_frequency == "yearly":
                monthly = monthly / 12
            total_monthly += monthly

            if monthly > 2000:  # > 2000 DOP/month
                recs.append(
                    {
                        "type": "cancel_subscription",
                        "title": f"Subscription costosa: {sub.name}",
                        "description": (
                            f"La suscripcion '{sub.name}' cuesta {monthly:.0f}/mes "
                            f"({monthly * 12:.0f}/ano). "
                            f"Considera si la usas lo suficiente para justificar el costo."
                        ),
                        "priority": "medium",
                        "estimated_savings": monthly,
                        "confidence": 0.6,
                        "features_used": {
                            "subscription_name": sub.name,
                            "monthly_cost": round(monthly, 2),
                            "billing_frequency": sub.billing_frequency,
                        },
                    }
                )

        if total_monthly > 5000:
            recs.append(
                {
                    "type": "reduce_spending",
                    "title": "Total de suscripciones elevado",
                    "description": (
                        f"Estas gastando {total_monthly:.0f}/mes en suscripciones. "
                        f"Esto representa un gasto fijo significativo."
                    ),
                    "priority": "medium",
                    "estimated_savings": round(total_monthly * 0.2, 2),
                    "confidence": 0.5,
                    "features_used": {
                        "total_monthly_subscriptions": round(total_monthly, 2),
                        "subscription_count": len(subscriptions),
                    },
                }
            )

        return recs

    # ==============================================================
    # 3. Savings Rate Check
    # ==============================================================

    async def _check_savings_rate(self, session: AsyncSession, user_id: uuid.UUID) -> list[dict]:
        """Check if savings rate is healthy (< 20% is flagged)."""
        recs: list[dict] = []
        today = date.today()
        month_start = today.replace(day=1)

        income_stmt = select(func.coalesce(func.sum(TransactionModel.amount), 0)).where(
            and_(
                TransactionModel.user_id == user_id,
                TransactionModel.deleted_at.is_(None),
                TransactionModel.transaction_type == "income",
                TransactionModel.status == "completed",
                TransactionModel.effective_date >= month_start,
            )
        )
        total_income = float((await session.execute(income_stmt)).scalar() or 0)

        expense_stmt = select(func.coalesce(func.sum(TransactionModel.amount), 0)).where(
            and_(
                TransactionModel.user_id == user_id,
                TransactionModel.deleted_at.is_(None),
                TransactionModel.transaction_type == "expense",
                TransactionModel.status == "completed",
                TransactionModel.effective_date >= month_start,
            )
        )
        total_expenses = float((await session.execute(expense_stmt)).scalar() or 0)

        if total_income > 0:
            savings_rate = (total_income - total_expenses) / total_income

            if savings_rate < 0.1:  # Less than 10%
                target_savings = total_income * 0.2
                current_savings = total_income - total_expenses
                gap = target_savings - current_savings

                recs.append(
                    {
                        "type": "increase_savings",
                        "title": f"Ratio de ahorro bajo ({savings_rate * 100:.0f}%)",
                        "description": (
                            f"Tu ratio de ahorro es {savings_rate * 100:.0f}%. "
                            f"El recomendado es 20%. "
                            f"Necesitas ahorrar {gap:.0f} mas por mes para alcanzar el 20%."
                        ),
                        "priority": "high",
                        "estimated_savings": max(0, gap),
                        "confidence": 0.85,
                        "features_used": {
                            "savings_rate": round(savings_rate, 4),
                            "total_income": round(total_income, 2),
                            "total_expenses": round(total_expenses, 2),
                            "target_savings_rate": 0.2,
                        },
                    }
                )

        return recs

    # ==============================================================
    # 4. Budget Utilization
    # ==============================================================

    async def _check_budget_utilization(
        self, session: AsyncSession, user_id: uuid.UUID
    ) -> list[dict]:
        """Check budget utilization (> 90% is flagged)."""
        recs: list[dict] = []
        today = date.today()

        stmt = select(BudgetModel).where(
            and_(
                BudgetModel.user_id == user_id,
                BudgetModel.is_active.is_(True),
                BudgetModel.deleted_at.is_(None),
            )
        )
        result = await session.execute(stmt)
        budgets = list(result.scalars().all())

        for budget in budgets:
            # Get spending for current month (all expenses, simplified)
            expense_stmt = select(func.coalesce(func.sum(TransactionModel.amount), 0)).where(
                and_(
                    TransactionModel.user_id == user_id,
                    TransactionModel.deleted_at.is_(None),
                    TransactionModel.transaction_type == "expense",
                    TransactionModel.status == "completed",
                    TransactionModel.effective_date >= today.replace(day=1),
                    TransactionModel.effective_date <= today,
                )
            )
            spent = float((await session.execute(expense_stmt)).scalar() or 0)
            limit = float(budget.amount)

            if limit > 0:
                utilization = spent / limit
                if utilization > 0.9:
                    recs.append(
                        {
                            "type": "budget_adjustment",
                            "title": f"Presupuesto '{budget.name}' al {utilization * 100:.0f}%",
                            "description": (
                                f"Has gastado {spent:.0f} de tu presupuesto de {limit:.0f} "
                                f"para '{budget.name}'. "
                                f"Te quedan {max(0, limit - spent):.0f}."
                            ),
                            "priority": "high" if utilization > 1.0 else "medium",
                            "estimated_savings": round(max(0, spent - limit * 0.8), 2),
                            "confidence": 0.9,
                            "features_used": {
                                "budget_name": budget.name,
                                "spent": round(spent, 2),
                                "limit": round(limit, 2),
                                "utilization": round(utilization, 4),
                            },
                        }
                    )

        return recs

    # ==============================================================
    # 5. Emergency Fund Check
    # ==============================================================

    async def _check_emergency_fund(self, session: AsyncSession, user_id: uuid.UUID) -> list[dict]:
        """Check if user has adequate emergency fund (< 6 months of expenses)."""
        recs: list[dict] = []
        today = date.today()

        # Total balance across all accounts
        balance_stmt = select(func.coalesce(func.sum(FinancialAccountModel.balance), 0)).where(
            and_(
                FinancialAccountModel.user_id == user_id,
                FinancialAccountModel.deleted_at.is_(None),
                FinancialAccountModel.include_in_net_worth.is_(True),
            )
        )
        total_balance = float((await session.execute(balance_stmt)).scalar() or 0)

        # Average monthly expenses (3 months)
        three_months_ago = today - timedelta(days=90)
        expense_stmt = select(func.coalesce(func.sum(TransactionModel.amount), 0)).where(
            and_(
                TransactionModel.user_id == user_id,
                TransactionModel.deleted_at.is_(None),
                TransactionModel.transaction_type == "expense",
                TransactionModel.status == "completed",
                TransactionModel.effective_date >= three_months_ago,
            )
        )
        total_expenses_3m = float((await session.execute(expense_stmt)).scalar() or 0)
        avg_monthly_expense = total_expenses_3m / 3

        if avg_monthly_expense > 0:
            months_covered = total_balance / avg_monthly_expense
            target_months = 6

            if months_covered < target_months:
                gap = (target_months - months_covered) * avg_monthly_expense
                recs.append(
                    {
                        "type": "build_emergency_fund",
                        "title": f"Fondo de emergencia insuficiente ({months_covered:.1f} meses)",
                        "description": (
                            f"Tu fondo de emergencia cubre {months_covered:.1f} meses "
                            f"de gastos. Se recomiendan {target_months} meses. "
                            f"Necesitas {gap:.0f} adicionales."
                        ),
                        "priority": "high" if months_covered < 2 else "medium",
                        "estimated_savings": round(gap, 2),
                        "confidence": 0.85,
                        "features_used": {
                            "total_balance": round(total_balance, 2),
                            "avg_monthly_expense": round(avg_monthly_expense, 2),
                            "months_covered": round(months_covered, 2),
                            "target_months": target_months,
                        },
                    }
                )

        return recs

    # ==============================================================
    # 6. Category Spending Analysis
    # ==============================================================

    async def _check_category_spending(
        self, session: AsyncSession, user_id: uuid.UUID
    ) -> list[dict]:
        """Analyze top spending categories for optimization opportunities."""
        recs: list[dict] = []
        today = date.today()
        month_start = today.replace(day=1)

        # Get top 3 spending categories this month
        from app.infrastructure.models.category import CategoryModel

        cat_stmt = (
            select(
                CategoryModel.name,
                func.sum(TransactionModel.amount).label("total"),
                func.count(TransactionModel.id).label("count"),
            )
            .join(TransactionModel, TransactionModel.category_id == CategoryModel.id)
            .where(
                and_(
                    TransactionModel.user_id == user_id,
                    TransactionModel.deleted_at.is_(None),
                    TransactionModel.transaction_type == "expense",
                    TransactionModel.status == "completed",
                    TransactionModel.effective_date >= month_start,
                )
            )
            .group_by(CategoryModel.name)
            .order_by(func.sum(TransactionModel.amount).desc())
            .limit(3)
        )
        result = await session.execute(cat_stmt)
        top_cats = result.all()

        # Get total expenses for context
        total_stmt = select(func.coalesce(func.sum(TransactionModel.amount), 0)).where(
            and_(
                TransactionModel.user_id == user_id,
                TransactionModel.deleted_at.is_(None),
                TransactionModel.transaction_type == "expense",
                TransactionModel.status == "completed",
                TransactionModel.effective_date >= month_start,
            )
        )
        total_expenses = float((await session.execute(total_stmt)).scalar() or 0)

        for cat_name, cat_total, cat_count in top_cats:
            cat_total_f = float(cat_total)
            if total_expenses > 0 and cat_total_f / total_expenses > 0.4:
                recs.append(
                    {
                        "type": "optimize_categories",
                        "title": f"Concentracion alta en '{cat_name}' ({cat_total_f / total_expenses * 100:.0f}%)",
                        "description": (
                            f"El {cat_total_f / total_expenses * 100:.0f}% de tu gasto "
                            f"va a '{cat_name}' ({cat_total_f:.0f} en {cat_count} transacciones). "
                            f"Revisa si hay oportunidades de reducir este gasto."
                        ),
                        "priority": "low",
                        "estimated_savings": round(cat_total_f * 0.1, 2),
                        "confidence": 0.5,
                        "features_used": {
                            "category_name": cat_name,
                            "category_total": round(cat_total_f, 2),
                            "category_count": cat_count,
                            "percentage_of_total": round(cat_total_f / total_expenses, 4),
                        },
                    }
                )

        return recs
