"""Risk assessor — evaluates user financial health and risk factors."""

from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal
from statistics import mean, stdev
from typing import Any

import structlog
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.models.budget import BudgetModel
from app.infrastructure.models.financial_account import FinancialAccountModel
from app.infrastructure.models.loan import LoanModel
from app.infrastructure.models.subscription import SubscriptionModel
from app.infrastructure.models.transaction import TransactionModel

logger = structlog.get_logger()

# Risk thresholds (DOP)
INCOME_VOLATILITY_THRESHOLD = 0.4  # CV > 0.4 = high risk
EXPENSE_VOLATILITY_THRESHOLD = 0.5  # CV > 0.5 = high risk
DTI_HEALTHY = 0.36  # DTI < 36% is healthy
DTI_RISKY = 0.50  # DTI > 50% is risky
EMERGENCY_MONTHS_TARGET = 6
BUDGET_OVERRUN_THRESHOLD = 0.8  # > 80% utilized = risk


class RiskAssessor:
    """Evaluates financial health and identifies risk factors."""

    async def assess(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
    ) -> dict[str, Any]:
        """Run full risk assessment.

        Returns:
        - risk_factors: list of identified risks with severity
        - financial_health_score: 0-100
        - metrics: all computed metrics
        - recommendations: risk-based recommendations
        """
        today = date.today()
        six_months_ago = today - timedelta(days=180)

        # Gather data
        income_vol = await self._compute_income_volatility(session, user_id, six_months_ago, today)
        expense_vol = await self._compute_expense_volatility(
            session, user_id, six_months_ago, today
        )
        dti = await self._compute_debt_to_income(session, user_id, today)
        emergency = await self._compute_emergency_fund(session, user_id, today)
        budget_risk = await self._compute_budget_risk(session, user_id, today)
        sub_creep = await self._compute_subscription_creep(session, user_id, today)

        metrics = {
            "income_volatility": income_vol,
            "expense_volatility": expense_vol,
            "debt_to_income": dti,
            "emergency_fund": emergency,
            "budget_risk": budget_risk,
            "subscription_creep": sub_creep,
        }

        risk_factors = self._identify_risks(metrics)
        health_score = self._compute_health_score(metrics, risk_factors)
        recommendations = self._generate_risk_recommendations(risk_factors, metrics)

        return {
            "financial_health_score": health_score,
            "risk_factors": risk_factors,
            "metrics": metrics,
            "recommendations": recommendations,
        }

    async def get_health_score(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
    ) -> dict[str, Any]:
        """Quick health score without full assessment."""
        result = await self.assess(session, user_id)
        return {
            "financial_health_score": result["financial_health_score"],
            "risk_count": len(
                [r for r in result["risk_factors"] if r["severity"] in ("high", "critical")]
            ),
            "top_risk": result["risk_factors"][0] if result["risk_factors"] else None,
        }

    # ---- Private helpers ----

    async def _compute_income_volatility(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
        start: date,
        end: date,
    ) -> dict[str, Any]:
        """Compute monthly income coefficient of variation."""
        month_trunc = func.date_trunc("month", TransactionModel.effective_date)
        stmt = (
            select(
                month_trunc.label("month"),
                func.sum(TransactionModel.amount).label("total"),
            )
            .where(
                and_(
                    TransactionModel.user_id == user_id,
                    TransactionModel.deleted_at.is_(None),
                    TransactionModel.transaction_type == "income",
                    TransactionModel.status == "completed",
                    TransactionModel.effective_date >= start,
                    TransactionModel.effective_date <= end,
                )
            )
            .group_by(month_trunc)
            .order_by(month_trunc)
        )
        result = await session.execute(stmt)
        rows = result.all()
        monthly_totals = [float(r.total) for r in rows]

        if len(monthly_totals) < 2:
            return {"cv": 0, "label": "insufficient_data", "months": len(monthly_totals)}

        avg = mean(monthly_totals)
        sd = stdev(monthly_totals)
        cv = sd / avg if avg > 0 else 0

        label = (
            "stable"
            if cv < 0.2
            else ("moderate" if cv < INCOME_VOLATILITY_THRESHOLD else "volatile")
        )

        return {
            "cv": round(cv, 4),
            "label": label,
            "avg_monthly": round(avg, 2),
            "months": len(monthly_totals),
        }

    async def _compute_expense_volatility(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
        start: date,
        end: date,
    ) -> dict[str, Any]:
        """Compute monthly expense coefficient of variation."""
        month_trunc = func.date_trunc("month", TransactionModel.effective_date)
        stmt = (
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
                    TransactionModel.effective_date >= start,
                    TransactionModel.effective_date <= end,
                )
            )
            .group_by(month_trunc)
            .order_by(month_trunc)
        )
        result = await session.execute(stmt)
        rows = result.all()
        monthly_totals = [float(r.total) for r in rows]

        if len(monthly_totals) < 2:
            return {"cv": 0, "label": "insufficient_data", "months": len(monthly_totals)}

        avg = mean(monthly_totals)
        sd = stdev(monthly_totals)
        cv = sd / avg if avg > 0 else 0

        label = (
            "stable"
            if cv < 0.25
            else ("moderate" if cv < EXPENSE_VOLATILITY_THRESHOLD else "volatile")
        )

        return {
            "cv": round(cv, 4),
            "label": label,
            "avg_monthly": round(avg, 2),
            "months": len(monthly_totals),
        }

    async def _compute_debt_to_income(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
        today: date,
    ) -> dict[str, Any]:
        """Compute debt-to-income ratio from active loans."""
        # Monthly income (last 3 months average)
        three_months_ago = today - timedelta(days=90)
        month_trunc = func.date_trunc("month", TransactionModel.effective_date)
        income_stmt = select(func.sum(TransactionModel.amount).label("total")).where(
            and_(
                TransactionModel.user_id == user_id,
                TransactionModel.deleted_at.is_(None),
                TransactionModel.transaction_type == "income",
                TransactionModel.status == "completed",
                TransactionModel.effective_date >= three_months_ago,
            )
        )
        income_result = await session.execute(income_stmt)
        total_income = float(income_result.scalar() or 0)
        avg_monthly_income = total_income / 3

        # Monthly loan payments
        loan_stmt = select(LoanModel).where(
            and_(
                LoanModel.user_id == user_id,
                LoanModel.status == "active",
                LoanModel.deleted_at.is_(None),
            )
        )
        loan_result = await session.execute(loan_stmt)
        loans = list(loan_result.scalars().all())
        total_monthly_payment = sum(float(l.monthly_payment or 0) for l in loans)

        if avg_monthly_income <= 0:
            return {
                "ratio": 0,
                "label": "no_income",
                "monthly_payment": total_monthly_payment,
                "avg_monthly_income": 0,
            }

        ratio = total_monthly_payment / avg_monthly_income

        if ratio < DTI_HEALTHY:
            label = "healthy"
        elif ratio < DTI_RISKY:
            label = "moderate"
        else:
            label = "risky"

        return {
            "ratio": round(ratio, 4),
            "label": label,
            "monthly_payment": round(total_monthly_payment, 2),
            "avg_monthly_income": round(avg_monthly_income, 2),
            "active_loans": len(loans),
        }

    async def _compute_emergency_fund(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
        today: date,
    ) -> dict[str, Any]:
        """Compute emergency fund adequacy (months of expenses covered)."""
        # Total balance
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

        if avg_monthly_expense <= 0:
            return {"months_covered": 0, "label": "no_data", "balance": total_balance}

        months_covered = total_balance / avg_monthly_expense

        if months_covered >= EMERGENCY_MONTHS_TARGET:
            label = "adequate"
        elif months_covered >= 3:
            label = "partial"
        else:
            label = "insufficient"

        return {
            "months_covered": round(months_covered, 2),
            "label": label,
            "balance": round(total_balance, 2),
            "avg_monthly_expense": round(avg_monthly_expense, 2),
            "target_months": EMERGENCY_MONTHS_TARGET,
        }

    async def _compute_budget_risk(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
        today: date,
    ) -> dict[str, Any]:
        """Compute budget overrun risk."""
        stmt = select(BudgetModel).where(
            and_(
                BudgetModel.user_id == user_id,
                BudgetModel.is_active.is_(True),
                BudgetModel.deleted_at.is_(None),
            )
        )
        result = await session.execute(stmt)
        budgets = list(result.scalars().all())

        if not budgets:
            return {"overrun_count": 0, "total_budgets": 0, "label": "no_budgets"}

        overrun_count = 0
        for b in budgets:
            limit = float(b.amount)
            spent = float(b.spent)
            if limit > 0 and (spent / limit) > BUDGET_OVERRUN_THRESHOLD:
                overrun_count += 1

        risk_ratio = overrun_count / len(budgets) if budgets else 0
        label = "low" if risk_ratio < 0.3 else ("moderate" if risk_ratio < 0.6 else "high")

        return {
            "overrun_count": overrun_count,
            "total_budgets": len(budgets),
            "risk_ratio": round(risk_ratio, 4),
            "label": label,
        }

    async def _compute_subscription_creep(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
        today: date,
    ) -> dict[str, Any]:
        """Compute subscription cost growth."""
        stmt = select(SubscriptionModel).where(
            and_(
                SubscriptionModel.user_id == user_id,
                SubscriptionModel.status == "active",
                SubscriptionModel.deleted_at.is_(None),
            )
        )
        result = await session.execute(stmt)
        subs = list(result.scalars().all())

        total_monthly = 0.0
        for sub in subs:
            monthly = float(sub.amount)
            if sub.billing_frequency == "yearly":
                monthly /= 12
            total_monthly += monthly

        # Estimate annual cost
        annual_cost = total_monthly * 12

        # Check if subscriptions are growing (compare start dates)
        recent_subs = [s for s in subs if s.start_date and (today - s.start_date).days < 180]
        older_subs = [s for s in subs if s.start_date and (today - s.start_date).days >= 180]

        recent_monthly = sum(
            float(s.amount) / 12 if s.billing_frequency == "yearly" else float(s.amount)
            for s in recent_subs
        )
        older_monthly = sum(
            float(s.amount) / 12 if s.billing_frequency == "yearly" else float(s.amount)
            for s in older_subs
        )

        if older_monthly > 0:
            growth_pct = ((total_monthly - older_monthly) / older_monthly) * 100
        else:
            growth_pct = 100.0 if total_monthly > 0 else 0.0

        return {
            "total_monthly": round(total_monthly, 2),
            "annual_cost": round(annual_cost, 2),
            "subscription_count": len(subs),
            "recent_count": len(recent_subs),
            "growth_percentage": round(growth_pct, 2),
            "label": "growing"
            if growth_pct > 20
            else ("stable" if growth_pct > -10 else "shrinking"),
        }

    def _identify_risks(self, metrics: dict[str, Any]) -> list[dict[str, Any]]:
        """Identify risk factors from computed metrics."""
        risks: list[dict[str, Any]] = []

        # Income volatility
        iv = metrics["income_volatility"]
        if iv["label"] == "volatile":
            risks.append(
                {
                    "factor": "income_volatility",
                    "severity": "high",
                    "title": "Ingreso volatile",
                    "description": (
                        f"Tus ingresos mensuales fluctuan significativamente "
                        f"(CV: {iv['cv']:.2f}). Esto dificulta el planeamiento financiero."
                    ),
                    "metric": iv["cv"],
                }
            )

        # Expense volatility
        ev = metrics["expense_volatility"]
        if ev["label"] == "volatile":
            risks.append(
                {
                    "factor": "expense_volatility",
                    "severity": "high",
                    "title": "Gasto volatile",
                    "description": (
                        f"Tus gastos mensuales fluctuan mucho "
                        f"(CV: {ev['cv']:.2f}). Intenta mantener gastos mas predecibles."
                    ),
                    "metric": ev["cv"],
                }
            )

        # Debt-to-income
        dti = metrics["debt_to_income"]
        if dti["label"] == "risky":
            risks.append(
                {
                    "factor": "debt_to_income",
                    "severity": "critical",
                    "title": "Ratio deuda/ingreso peligroso",
                    "description": (
                        f"Tus pagos de deuda ({dti['monthly_payment']:.0f}/mes) "
                        f"representan el {dti['ratio'] * 100:.0f}% de tus ingresos. "
                        f"Se recomienda menos del 36%."
                    ),
                    "metric": dti["ratio"],
                }
            )
        elif dti["label"] == "moderate":
            risks.append(
                {
                    "factor": "debt_to_income",
                    "severity": "medium",
                    "title": "Ratio deuda/ingreso moderado",
                    "description": (
                        f"Tus pagos de deuda representan el {dti['ratio'] * 100:.0f}% "
                        f"de tus ingresos. Cerca del limite recomendado del 36%."
                    ),
                    "metric": dti["ratio"],
                }
            )

        # Emergency fund
        ef = metrics["emergency_fund"]
        if ef["label"] == "insufficient":
            risks.append(
                {
                    "factor": "emergency_fund",
                    "severity": "high",
                    "title": "Fondo de emergencia insuficiente",
                    "description": (
                        f"Tu fondo cubre {ef['months_covered']:.1f} meses de gastos. "
                        f"Se recomiendan al menos 6 meses."
                    ),
                    "metric": ef["months_covered"],
                }
            )
        elif ef["label"] == "partial":
            risks.append(
                {
                    "factor": "emergency_fund",
                    "severity": "medium",
                    "title": "Fondo de emergencia parcial",
                    "description": (
                        f"Tu fondo cubre {ef['months_covered']:.1f} meses. "
                        f"Es un buen inicio, pero se recomiendan 6 meses."
                    ),
                    "metric": ef["months_covered"],
                }
            )

        # Budget overrun
        br = metrics["budget_risk"]
        if br["label"] == "high":
            risks.append(
                {
                    "factor": "budget_overrun",
                    "severity": "high",
                    "title": "Varios presupuestos excedidos",
                    "description": (
                        f"{br['overrun_count']} de {br['total_budgets']} "
                        f"presupuestos estan al >80% de su limite."
                    ),
                    "metric": br["risk_ratio"],
                }
            )

        # Subscription creep
        sc = metrics["subscription_creep"]
        if sc["label"] == "growing":
            risks.append(
                {
                    "factor": "subscription_creep",
                    "severity": "medium",
                    "title": "Costo de suscripciones creciendo",
                    "description": (
                        f"Tus suscripciones crecieron {sc['growth_percentage']:.0f}% "
                        f"recientemente. Total: {sc['total_monthly']:.0f}/mes."
                    ),
                    "metric": sc["growth_percentage"],
                }
            )

        # Sort by severity
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        risks.sort(key=lambda r: severity_order.get(r["severity"], 4))

        return risks

    def _compute_health_score(
        self,
        metrics: dict[str, Any],
        risk_factors: list[dict[str, Any]],
    ) -> int:
        """Compute composite financial health score (0-100).

        Weights:
        - Income stability: 15 points
        - Expense stability: 15 points
        - Debt health: 20 points
        - Emergency fund: 20 points
        - Budget adherence: 15 points
        - Subscription control: 15 points
        """
        score = 100

        # Income volatility penalty
        iv = metrics["income_volatility"]
        if iv["label"] == "volatile":
            score -= 10
        elif iv["label"] == "moderate":
            score -= 5

        # Expense volatility penalty
        ev = metrics["expense_volatility"]
        if ev["label"] == "volatile":
            score -= 10
        elif ev["label"] == "moderate":
            score -= 5

        # Debt-to-income penalty
        dti = metrics["debt_to_income"]
        if dti["label"] == "risky":
            score -= 15
        elif dti["label"] == "moderate":
            score -= 7

        # Emergency fund bonus/penalty
        ef = metrics["emergency_fund"]
        if ef["label"] == "adequate":
            pass  # no penalty
        elif ef["label"] == "partial":
            score -= 8
        else:
            score -= 15

        # Budget risk penalty
        br = metrics["budget_risk"]
        if br["label"] == "high":
            score -= 10
        elif br["label"] == "moderate":
            score -= 5

        # Subscription creep penalty
        sc = metrics["subscription_creep"]
        if sc["label"] == "growing":
            score -= 7

        # Extra penalty per critical/high risk factor
        for risk in risk_factors:
            if risk["severity"] == "critical":
                score -= 5
            elif risk["severity"] == "high":
                score -= 3

        return max(0, min(100, score))

    def _generate_risk_recommendations(
        self,
        risk_factors: list[dict[str, Any]],
        metrics: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Generate risk-based recommendations."""
        recs: list[dict[str, Any]] = []

        for risk in risk_factors:
            if risk["factor"] == "income_volatility":
                recs.append(
                    {
                        "type": "income_volatility",
                        "title": "Estabiliza tu ingreso",
                        "description": (
                            "Considera fuentes de ingreso adicionales o "
                            "negociar un salario fijo para reducir la volatilidad."
                        ),
                        "priority": "high",
                        "estimated_savings": 0,
                        "confidence": 0.7,
                        "risk_factor": risk["factor"],
                    }
                )
            elif risk["factor"] == "emergency_fund":
                ef = metrics["emergency_fund"]
                gap = max(
                    0, (ef["target_months"] - ef["months_covered"]) * ef["avg_monthly_expense"]
                )
                recs.append(
                    {
                        "type": "build_emergency_fund",
                        "title": "Construye tu fondo de emergencia",
                        "description": (
                            f"Necesitas {gap:.0f} adicionales para tener "
                            f"6 meses de gastos de emergencia."
                        ),
                        "priority": "high",
                        "estimated_savings": round(gap, 2),
                        "confidence": 0.85,
                        "risk_factor": risk["factor"],
                    }
                )
            elif risk["factor"] == "debt_to_income":
                recs.append(
                    {
                        "type": "pay_debt",
                        "title": "Reduce tu carga de deuda",
                        "description": (
                            "Tu ratio de deuda/ingreso es alto. "
                            "Prioriza pagar deudas con mayor tasa de interes."
                        ),
                        "priority": "high",
                        "estimated_savings": round(
                            metrics["debt_to_income"]["monthly_payment"] * 0.3, 2
                        ),
                        "confidence": 0.8,
                        "risk_factor": risk["factor"],
                    }
                )
            elif risk["factor"] == "budget_overrun":
                recs.append(
                    {
                        "type": "budget_adjustment",
                        "title": "Ajusta tus presupuestos",
                        "description": (
                            "Varios de tus presupuestos estan cerca del limite. "
                            "Revisa tus gastos o ajusta los montos."
                        ),
                        "priority": "medium",
                        "estimated_savings": 0,
                        "confidence": 0.75,
                        "risk_factor": risk["factor"],
                    }
                )
            elif risk["factor"] == "subscription_creep":
                recs.append(
                    {
                        "type": "cancel_subscription",
                        "title": "Revisa tus suscripciones",
                        "description": (
                            "El costo de tus suscripciones esta creciendo. "
                            "Evalua cuales realmente necesitas."
                        ),
                        "priority": "medium",
                        "estimated_savings": round(
                            metrics["subscription_creep"]["total_monthly"] * 0.2, 2
                        ),
                        "confidence": 0.6,
                        "risk_factor": risk["factor"],
                    }
                )

        return recs
