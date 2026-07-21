"""Habit analyzer — tracks and analyzes user spending habits."""

from __future__ import annotations

import uuid
from collections import Counter, defaultdict
from datetime import date, timedelta
from decimal import Decimal
from statistics import mean, stdev
from typing import Any

import structlog
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.models.transaction import TransactionModel

logger = structlog.get_logger()

# Days of week for pattern detection
WEEKEND_DAYS = {5, 6}  # Saturday=5, Sunday=6 (Python weekday)


class HabitAnalyzer:
    """Analyzes user spending habits from transaction history."""

    async def analyze(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
        months: int = 6,
    ) -> dict[str, Any]:
        """Run full habit analysis for a user.

        Returns a dict with:
        - spending_frequency: per-category frequency scores
        - spending_patterns: weekend/weekday/payday patterns
        - habit_stability: coefficient of variation per category
        - category_dominance: top categories by share
        - detected_recurring: potential subscriptions not yet tracked
        - overall_habit_score: 0-100 habit health score
        - recommendations: list of habit-based recommendations
        """
        today = date.today()
        start_date = today - timedelta(days=months * 30)

        transactions = await self._get_transactions(session, user_id, start_date, today)
        expenses = [t for t in transactions if t.transaction_type == "expense"]

        if not expenses:
            return {
                "spending_frequency": {},
                "spending_patterns": {},
                "habit_stability": {},
                "category_dominance": {},
                "detected_recurring": [],
                "overall_habit_score": 0,
                "recommendations": [],
                "message": "No hay transacciones suficientes para analizar habitos.",
            }

        spending_frequency = self._compute_spending_frequency(expenses, months)
        spending_patterns = self._compute_spending_patterns(expenses)
        habit_stability = self._compute_habit_stability(expenses, months)
        category_dominance = self._compute_category_dominance(expenses)
        detected_recurring = await self._detect_recurring_expenses(session, user_id, expenses)
        habit_score = self._compute_habit_score(
            spending_frequency, habit_stability, category_dominance
        )
        recommendations = self._generate_habit_recommendations(
            spending_frequency,
            spending_patterns,
            habit_stability,
            category_dominance,
            detected_recurring,
            habit_score,
        )

        return {
            "spending_frequency": spending_frequency,
            "spending_patterns": spending_patterns,
            "habit_stability": habit_stability,
            "category_dominance": category_dominance,
            "detected_recurring": detected_recurring,
            "overall_habit_score": habit_score,
            "recommendations": recommendations,
        }

    async def get_trends(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
        months: int = 6,
    ) -> dict[str, Any]:
        """Get spending trends by category over time.

        Returns monthly totals per category + trend direction.
        """
        today = date.today()
        start_date = today - timedelta(days=months * 30)

        # Get monthly expense totals per category
        from app.infrastructure.models.category import CategoryModel

        month_trunc = func.date_trunc("month", TransactionModel.effective_date)
        stmt = (
            select(
                month_trunc.label("month"),
                CategoryModel.name.label("category"),
                func.sum(TransactionModel.amount).label("total"),
            )
            .join(CategoryModel, TransactionModel.category_id == CategoryModel.id)
            .where(
                and_(
                    TransactionModel.user_id == user_id,
                    TransactionModel.deleted_at.is_(None),
                    TransactionModel.transaction_type == "expense",
                    TransactionModel.status == "completed",
                    TransactionModel.effective_date >= start_date,
                )
            )
            .group_by(month_trunc, CategoryModel.name)
            .order_by(month_trunc, CategoryModel.name)
        )
        result = await session.execute(stmt)
        rows = result.all()

        # Build monthly data
        monthly_by_cat: dict[str, list[tuple[str, float]]] = defaultdict(list)
        for month_dt, cat_name, total in rows:
            month_key = month_dt.strftime("%Y-%m")
            monthly_by_cat[cat_name].append((month_key, float(total)))

        # Compute trends
        trends: dict[str, dict[str, Any]] = {}
        for cat_name, entries in monthly_by_cat.items():
            values = [v for _, v in entries]
            if len(values) >= 2:
                recent_avg = mean(values[-3:]) if len(values) >= 3 else values[-1]
                older_avg = mean(values[:-3]) if len(values) > 3 else values[0]
                if older_avg > 0:
                    change_pct = ((recent_avg - older_avg) / older_avg) * 100
                else:
                    change_pct = 100.0 if recent_avg > 0 else 0.0
                trend = (
                    "increasing"
                    if change_pct > 10
                    else ("decreasing" if change_pct < -10 else "stable")
                )
            else:
                change_pct = 0.0
                trend = "insufficient_data"

            trends[cat_name] = {
                "monthly_data": {m: round(v, 2) for m, v in entries},
                "total": round(sum(values), 2),
                "average": round(mean(values), 2),
                "trend": trend,
                "change_percentage": round(change_pct, 2),
            }

        return {"trends": trends, "months_analyzed": months}

    # ---- Private helpers ----

    async def _get_transactions(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
        start_date: date,
        end_date: date,
    ) -> list[TransactionModel]:
        """Fetch transactions in the date range."""
        stmt = (
            select(TransactionModel)
            .where(
                and_(
                    TransactionModel.user_id == user_id,
                    TransactionModel.deleted_at.is_(None),
                    TransactionModel.transaction_type.in_(["expense", "income"]),
                    TransactionModel.status == "completed",
                    TransactionModel.effective_date >= start_date,
                    TransactionModel.effective_date <= end_date,
                )
            )
            .order_by(TransactionModel.effective_date)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    def _compute_spending_frequency(
        self, expenses: list[TransactionModel], months: int
    ) -> dict[str, Any]:
        """Compute per-category spending frequency (transactions per week)."""
        cat_days: dict[str, set[str]] = defaultdict(set)
        cat_counts: dict[str, int] = Counter()

        for t in expenses:
            cat = str(t.category_id) if t.category_id else "uncategorized"
            day_str = t.effective_date.isoformat()
            cat_days[cat].add(day_str)
            cat_counts[cat] += 1

        weeks = max(1, months * 4)
        frequency: dict[str, Any] = {}
        for cat, days_set in cat_days.items():
            unique_days = len(days_set)
            tx_count = cat_counts[cat]
            freq_per_week = round(tx_count / weeks, 2)
            # Score: 0=never, 1=daily, 0.5=twice a week
            score = min(1.0, freq_per_week / 7.0)
            frequency[cat] = {
                "transactions_per_week": freq_per_week,
                "unique_days": unique_days,
                "total_transactions": tx_count,
                "frequency_score": round(score, 3),
                "frequency_label": self._frequency_label(freq_per_week),
            }

        return frequency

    def _frequency_label(self, per_week: float) -> str:
        if per_week >= 5:
            return "diario"
        if per_week >= 2:
            return "frecuente"
        if per_week >= 0.5:
            return "regular"
        if per_week > 0:
            return "ocasional"
        return "sin actividad"

    def _compute_spending_patterns(self, expenses: list[TransactionModel]) -> dict[str, Any]:
        """Detect weekend vs weekday patterns and payday spikes."""
        weekday_amounts: list[float] = []
        weekend_amounts: list[float] = []
        weekday_count = 0
        weekend_count = 0

        for t in expenses:
            amount = float(t.amount)
            if t.effective_date.weekday() in WEEKEND_DAYS:
                weekend_amounts.append(amount)
                weekend_count += 1
            else:
                weekday_amounts.append(amount)
                weekday_count += 1

        avg_weekday = mean(weekday_amounts) if weekday_amounts else 0
        avg_weekend = mean(weekend_amounts) if weekend_amounts else 0
        total_tx = weekday_count + weekend_count

        weekend_share = weekend_count / total_tx if total_tx > 0 else 0
        weekend_amount_share = (
            sum(weekend_amounts) / (sum(weekday_amounts) + sum(weekend_amounts))
            if (weekday_amounts or weekend_amounts)
            else 0
        )

        return {
            "weekday_transactions": weekday_count,
            "weekend_transactions": weekend_count,
            "avg_weekday_amount": round(avg_weekday, 2),
            "avg_weekend_amount": round(avg_weekend, 2),
            "weekend_transaction_share": round(weekend_share, 3),
            "weekend_amount_share": round(weekend_amount_share, 3),
            "high_weekend_spending": weekend_amount_share > 0.35,
        }

    def _compute_habit_stability(
        self, expenses: list[TransactionModel], months: int
    ) -> dict[str, Any]:
        """Compute coefficient of variation per category (lower = more stable)."""
        cat_monthly: dict[str, list[float]] = defaultdict(list)
        for t in expenses:
            cat = str(t.category_id) if t.category_id else "uncategorized"
            month_key = t.effective_date.strftime("%Y-%m")
            cat_monthly[cat].append(float(t.amount))

        # Aggregate by month
        cat_month_totals: dict[str, list[float]] = defaultdict(list)
        for cat, amounts in cat_monthly.items():
            # amounts are all transactions for that category in a month
            cat_month_totals[cat].append(sum(amounts))

        stability: dict[str, Any] = {}
        for cat, monthly_totals in cat_month_totals.items():
            if len(monthly_totals) >= 2:
                avg = mean(monthly_totals)
                sd = stdev(monthly_totals)
                cv = sd / avg if avg > 0 else 0
            else:
                cv = 0

            # Score: CV < 0.3 = very stable, > 1.0 = very volatile
            if cv < 0.3:
                label = "muy_estable"
            elif cv < 0.5:
                label = "estable"
            elif cv < 1.0:
                label = "variable"
            else:
                label = "muy_variable"

            stability[cat] = {
                "cv": round(cv, 4),
                "label": label,
                "months_of_data": len(monthly_totals),
            }

        return stability

    def _compute_category_dominance(self, expenses: list[TransactionModel]) -> dict[str, Any]:
        """Compute which categories dominate spending."""
        cat_totals: dict[str, float] = defaultdict(float)
        total = 0.0
        for t in expenses:
            cat = str(t.category_id) if t.category_id else "uncategorized"
            amount = float(t.amount)
            cat_totals[cat] += amount
            total += amount

        dominance: dict[str, Any] = {}
        sorted_cats = sorted(cat_totals.items(), key=lambda x: x[1], reverse=True)
        for rank, (cat, cat_total) in enumerate(sorted_cats, 1):
            share = cat_total / total if total > 0 else 0
            dominance[cat] = {
                "total": round(cat_total, 2),
                "share": round(share, 4),
                "rank": rank,
                "is_dominant": share > 0.4,
            }

        return dominance

    async def _detect_recurring_expenses(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
        expenses: list[TransactionModel],
    ) -> list[dict[str, Any]]:
        """Detect potential subscriptions from recurring expense patterns."""
        # Group by category + approximate amount
        cat_amounts: dict[str, dict[float, list[date]]] = defaultdict(lambda: defaultdict(list))
        for t in expenses:
            cat = str(t.category_id) if t.category_id else "uncategorized"
            # Round amount to nearest 100 for grouping
            rounded_amount = round(float(t.amount) / 100) * 100
            cat_amounts[cat][rounded_amount].append(t.effective_date)

        recurring: list[dict[str, Any]] = []
        for cat, amounts_map in cat_amounts.items():
            for amount, dates_list in amounts_map.items():
                if len(dates_list) < 3:
                    continue
                # Check if dates are roughly monthly (25-35 day gaps)
                sorted_dates = sorted(dates_list)
                gaps = [
                    (sorted_dates[i + 1] - sorted_dates[i]).days
                    for i in range(len(sorted_dates) - 1)
                ]
                avg_gap = mean(gaps) if gaps else 0
                if 20 <= avg_gap <= 40:
                    recurring.append(
                        {
                            "category_id": cat,
                            "approximate_amount": amount,
                            "occurrences": len(dates_list),
                            "avg_days_between": round(avg_gap, 1),
                            "confidence": min(1.0, len(dates_list) / 6),
                        }
                    )

        return recurring

    def _compute_habit_score(
        self,
        frequency: dict[str, Any],
        stability: dict[str, Any],
        dominance: dict[str, Any],
    ) -> int:
        """Compute overall habit health score (0-100).

        Higher = healthier habits (more stable, less concentrated).
        """
        score = 50  # baseline

        # Stability bonus: many stable categories = good
        stable_cats = sum(1 for s in stability.values() if s["label"] in ("muy_estable", "estable"))
        total_cats = max(1, len(stability))
        stability_ratio = stable_cats / total_cats
        score += int(stability_ratio * 25)

        # Dominance penalty: one category > 40% = bad
        dominant_count = sum(1 for d in dominance.values() if d["is_dominant"])
        score -= dominant_count * 10

        # Frequency bonus: active tracking = good
        active_cats = sum(1 for f in frequency.values() if f["total_transactions"] >= 3)
        freq_ratio = active_cats / max(1, len(frequency))
        score += int(freq_ratio * 15)

        return max(0, min(100, score))

    def _generate_habit_recommendations(
        self,
        frequency: dict[str, Any],
        patterns: dict[str, Any],
        stability: dict[str, Any],
        dominance: dict[str, Any],
        detected_recurring: list[dict[str, Any]],
        habit_score: int,
    ) -> list[dict[str, Any]]:
        """Generate habit-based recommendations."""
        recs: list[dict[str, Any]] = []

        # High weekend spending
        if patterns.get("high_weekend_spending"):
            recs.append(
                {
                    "type": "spending_pattern",
                    "title": "Gasto elevado en fin de semana",
                    "description": (
                        f"El {patterns['weekend_amount_share'] * 100:.0f}% de tu gasto "
                        f"ocurre en fin de semana, con un promedio de "
                        f"{patterns['avg_weekend_amount']:.0f} por transaccion."
                    ),
                    "priority": "medium",
                    "estimated_savings": round(
                        patterns["avg_weekend_amount"] * patterns["weekend_transactions"] * 0.15, 2
                    ),
                    "confidence": 0.7,
                    "category": "spending_pattern",
                    "features_used": patterns,
                }
            )

        # Category dominance
        for cat, info in dominance.items():
            if info["is_dominant"]:
                recs.append(
                    {
                        "type": "optimize_categories",
                        "title": f"Concentracion alta en categoria {cat[:8]}",
                        "description": (
                            f"Una categoria concentra el {info['share'] * 100:.0f}% "
                            f"de tu gasto ({info['total']:.0f}). "
                            f"Revisa si puedes reducir o redistribuir este gasto."
                        ),
                        "priority": "medium",
                        "estimated_savings": round(info["total"] * 0.1, 2),
                        "confidence": 0.65,
                        "category": "category_dominance",
                        "features_used": info,
                    }
                )

        # Unstable categories
        for cat, info in stability.items():
            if info["label"] == "muy_variable" and info["months_of_data"] >= 3:
                recs.append(
                    {
                        "type": "habit_optimization",
                        "title": f"Gasto inestable en categoria {cat[:8]}",
                        "description": (
                            f"Tu gasto en esta categoria fluctua mucho "
                            f"(CV: {info['cv']:.2f}). "
                            f"Considera establecer un presupuesto fijo."
                        ),
                        "priority": "low",
                        "estimated_savings": 0,
                        "confidence": 0.5,
                        "category": "habit_stability",
                        "features_used": info,
                    }
                )

        # Detected recurring expenses
        for rec in detected_recurring:
            if rec["confidence"] >= 0.5:
                recs.append(
                    {
                        "type": "subscription_creep",
                        "title": f"Gasto recurrente detectado (~{rec['approximate_amount']:.0f})",
                        "description": (
                            f"Detectamos un patron de gasto recurrente de ~"
                            f"{rec['approximate_amount']:.0f} cada "
                            f"{rec['avg_days_between']:.0f} dias "
                            f"({rec['occurrences']} veces). "
                            f"Podria ser una suscripcion no registrada."
                        ),
                        "priority": "low",
                        "estimated_savings": 0,
                        "confidence": round(rec["confidence"], 2),
                        "category": "detected_recurring",
                        "features_used": rec,
                    }
                )

        return recs
