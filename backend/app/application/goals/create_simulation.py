"""Use case: Create a what-if simulation for a goal."""

from __future__ import annotations

import random
from datetime import date as date_type, timedelta
from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.goal_repository import GoalRepository

if TYPE_CHECKING:
    import uuid
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()

MONTHLY_KEYS = {"monthly"}
QUARTERLY_KEYS = {"quarterly"}
QUADRIMESTRAL_KEYS = {"quadrimestral"}
YEARLY_KEYS = {"yearly"}
ONE_TIME_KEYS = {"one_time"}


def _calc_monthly_amount(
    amount: float,
    frequency: str,
    growth_rate: float | None,
    months_elapsed: int,
    start_month: int | None = None,
) -> float:
    """Monto del ingreso/gasto en un mes dado.

    `amount` es el monto por ocurrencia (ej: bono anual 31,525), NO un monto
    mensual equivalente. El periodo se ancla en ``start_month`` (mes relativo
    1 = inicio del goal) para que un bono que cae en un mes arbitrario del
    horizonte se acredite correctamente incluso en horizontes cortos.
    """
    base = amount
    if growth_rate and months_elapsed > 0:
        base *= (1 + growth_rate / 100) ** (months_elapsed / 12)
    anchor = start_month if start_month else 1
    if frequency in MONTHLY_KEYS:
        return base
    if frequency in QUARTERLY_KEYS:
        return base if (months_elapsed - anchor) % 3 == 0 else 0.0
    if frequency in QUADRIMESTRAL_KEYS:
        return base if (months_elapsed - anchor) % 4 == 0 else 0.0
    if frequency in YEARLY_KEYS:
        return base if (months_elapsed - anchor) % 12 == 0 else 0.0
    if frequency in ONE_TIME_KEYS:
        return base if months_elapsed == anchor else 0.0
    return 0.0


def _is_active(month: int, start_month: int | None, end_month: int | None) -> bool:
    if start_month and month < start_month:
        return False
    if end_month and month > end_month:
        return False
    return True


class CreateSimulationUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = GoalRepository(session)

    async def execute(
        self, user_id: uuid.UUID, goal_id: uuid.UUID, *,
        name: str, monthly_contribution: float,
        lump_sum: float | None = None,
        lump_sum_date: str | None = None,
        interest_rate: float | None = None,
        increase_pct: float | None = None,
        inflation_rate: float | None = None,
        income_sources: list[dict] | None = None,
        expenses: list[dict] | None = None,
        enable_monte_carlo: bool = False,
        notes: str | None = None,
        preview: bool = False,
    ) -> dict:
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

        current_amount = float(goal.current_amount)

        # Parse income sources and expenses
        inc_sources = income_sources or []
        exp_items = expenses or []
        infl = float(inflation_rate) / 100 if inflation_rate else 0.0
        inc_pct = float(increase_pct) / 100 if increase_pct else 0.0

        # Normalizar fecha de lump sum (acepta "YYYY-MM" o "YYYY-MM-DD")
        ls_date: date_type | None = None
        if lump_sum_date:
            try:
                ls_date = date_type.fromisoformat(lump_sum_date[:7] + "-01" if len(lump_sum_date) == 7 else lump_sum_date)
            except ValueError:
                ls_date = None

        # Run main projection
        projection, total_contrib, total_interest, months, final_prob = self._run_projection(
            target_amount=float(goal.target_amount),
            current_amount=float(goal.current_amount),
            monthly=monthly_contribution,
            rate=interest_rate or 0,
            lump_sum=lump_sum,
            lump_sum_date=lump_sum_date,
            increase_pct=inc_pct,
            inflation_rate=infl,
            income_sources=inc_sources,
            expenses=exp_items,
            start_date=goal.start_date,
            target_date=goal.target_date,
        )

        # Monte Carlo
        mc_data = None
        if enable_monte_carlo:
            mc_data = self._run_monte_carlo(
                target_amount=float(goal.target_amount),
                current_amount=float(goal.current_amount),
                monthly=monthly_contribution,
                rate=interest_rate or 0,
                lump_sum=lump_sum,
                lump_sum_date=lump_sum_date,
                increase_pct=inc_pct,
                inflation_rate=infl,
                income_sources=inc_sources,
                expenses=exp_items,
                start_date=goal.start_date,
                target_date=goal.target_date,
                num_simulations=500,
            )

        # Recommendations
        recommendations = self._calc_recommendations(
            target_amount=float(goal.target_amount),
            current_amount=float(goal.current_amount),
            current_monthly=monthly_contribution,
            rate=interest_rate or 0,
            inflation_rate=infl,
            start_date=goal.start_date,
            target_date=goal.target_date,
        )

        predicted_date = goal.start_date + timedelta(days=int(months * 30.44))
        predicted_prob = round(final_prob, 4)
        total_contributions = round(total_contrib, 2)
        total_interest_val = round(total_interest, 2)
        total_income_used = round(
            sum(p.get("income_contribution", 0) for p in projection), 2
        ) if projection else 0

        if preview:
            logger.info(
                "simulation_previewed",
                user_id=str(user_id), goal_id=str(goal_id),
                months=months, probability=predicted_prob,
                income_sources=len(inc_sources), expenses=len(exp_items),
            )
            return {
                "id": None, "saved": False, "name": name.strip(),
                "goal_id": str(goal.id), "goal_name": goal.name,
                "starting_amount": f"{current_amount:.2f}",
                "monthly_contribution": str(monthly_contribution),
                "lump_sum": str(lump_sum) if lump_sum else None,
                "lump_sum_date": lump_sum_date,
                "interest_rate": str(interest_rate) if interest_rate else None,
                "increase_pct": str(increase_pct) if increase_pct else None,
                "inflation_rate": str(inflation_rate) if inflation_rate else None,
                "income_sources": inc_sources,
                "expenses": exp_items,
                "predicted_completion_date": predicted_date.isoformat(),
                "predicted_probability": predicted_prob,
                "total_contributions": str(total_contributions),
                "total_interest": str(total_interest_val),
                "total_income_used": str(total_income_used),
                "months_to_complete": months,
                "projection": projection,
                "monte_carlo": mc_data,
                "recommendations": recommendations,
                "notes": notes,
                "created_at": None,
            }

        store_projection = {
            "months": projection,
            "params": {
                "inflation_rate": float(inflation_rate) if inflation_rate else None,
                "income_sources": inc_sources,
                "expenses": exp_items,
                "enable_monte_carlo": enable_monte_carlo,
                "increase_pct": float(increase_pct) if increase_pct else None,
            },
            "monte_carlo": mc_data,
            "recommendations": recommendations,
            "total_income_used": total_income_used,
        }

        sim = await self._repo.create_simulation(
            user_id, goal_id=goal.id, name=name.strip(),
            monthly_contribution=monthly_contribution,
            lump_sum=lump_sum,
            lump_sum_date=ls_date,
            interest_rate=interest_rate,
            increase_pct=increase_pct,
            predicted_completion_date=predicted_date,
            predicted_probability=predicted_prob,
            total_contributions=total_contributions,
            total_interest=total_interest_val,
            months_to_complete=months,
            projection=store_projection,
            notes=notes,
        )

        logger.info(
            "simulation_created",
            user_id=str(user_id), goal_id=str(goal_id),
            months=months, probability=predicted_prob,
            income_sources=len(inc_sources), expenses=len(exp_items),
        )

        return {
            "id": str(sim.id), "saved": True, "name": sim.name,
            "goal_id": str(goal.id), "goal_name": goal.name,
            "starting_amount": f"{current_amount:.2f}",
            "monthly_contribution": str(sim.monthly_contribution),
            "lump_sum": str(sim.lump_sum) if sim.lump_sum else None,
            "lump_sum_date": sim.lump_sum_date.isoformat() if sim.lump_sum_date else None,
            "interest_rate": str(sim.interest_rate) if sim.interest_rate else None,
            "increase_pct": str(sim.increase_pct) if sim.increase_pct else None,
            "inflation_rate": str(inflation_rate) if inflation_rate else None,
            "income_sources": inc_sources,
            "expenses": exp_items,
            "predicted_completion_date": predicted_date.isoformat(),
            "predicted_probability": predicted_prob,
            "total_contributions": str(total_contributions),
            "total_interest": str(total_interest_val),
            "total_income_used": str(total_income_used),
            "months_to_complete": months,
            "projection": projection,
            "monte_carlo": mc_data,
            "recommendations": recommendations,
            "notes": sim.notes,
            "created_at": sim.created_at.isoformat() if sim.created_at else None,
        }

    @staticmethod
    def _current_month_relative(start_date: date_type) -> int:
        """Mes relativo de hoy respecto al inicio del goal (mes 1 = inicio)."""
        today = date_type.today()
        rel = (today.year - start_date.year) * 12 + (today.month - start_date.month) + 1
        return max(rel, 1)

    def _run_projection(
        self, target_amount: float, current_amount: float,
        monthly: float, rate: float,
        lump_sum: float | None, lump_sum_date: str | None,
        increase_pct: float, inflation_rate: float,
        income_sources: list[dict], expenses: list[dict],
        start_date: date_type, target_date: date_type,
    ) -> tuple[list[dict], float, float, int, float]:
        monthly_rate = rate / 100 / 12
        balance = current_amount
        months = 0
        projection = []
        total_contrib = 0.0
        total_interest = 0.0
        lump_applied = False

        anchor_now = self._current_month_relative(start_date)

        ls_month: int | None = None
        if lump_sum_date:
            try:
                ls_dt = date_type.fromisoformat(lump_sum_date)
                ls_month = (ls_dt.year - start_date.year) * 12 + (ls_dt.month - start_date.month)
                if ls_month < 1:
                    ls_month = 1
            except ValueError:
                ls_month = None

        adj_target = target_amount

        while balance < adj_target and months < 600:
            months += 1

            # Escalamiento de aportacion
            contribution = monthly
            if increase_pct > 0 and months > 1:
                contribution = monthly * (1 + increase_pct * ((months - 1) / 12))

            # Lump sum
            if lump_sum and ls_month and not lump_applied and months >= ls_month:
                contribution += lump_sum
                lump_applied = True

            # Income sources
            income_amount = 0.0
            for src in income_sources:
                sm = src.get("start_month") or anchor_now
                em = src.get("end_month")
                if _is_active(months, sm, em):
                    income_amount += _calc_monthly_amount(
                        float(src["amount"]), src["frequency"],
                        src.get("growth_rate"), months, sm,
                    )

            # Expenses
            expense_amount = 0.0
            for exp in expenses:
                sm = exp.get("start_month") or anchor_now
                em = exp.get("end_month")
                if _is_active(months, sm, em):
                    expense_amount += _calc_monthly_amount(
                        float(exp["amount"]), exp["frequency"],
                        exp.get("growth_rate"), months, sm,
                    )

            # Net total for this month
            total_in = contribution + income_amount
            net = total_in - expense_amount
            if net < 0:
                net = 0

            # Inflation-adjusted target
            if inflation_rate > 0:
                adj_target = target_amount * (1 + inflation_rate) ** (months / 12)

            interest = balance * monthly_rate
            balance = balance + net + interest
            total_contrib += contribution
            total_interest += interest

            projection.append({
                "month": months,
                "contribution": round(contribution, 2),
                "interest": round(interest, 2),
                "cumulative": round(balance, 2),
                "income_contribution": round(income_amount, 2) if income_amount > 0 else 0,
                "inflation_adjusted_target": round(adj_target, 2) if inflation_rate > 0 else 0,
                "date": (start_date + timedelta(days=months * 30.44)).isoformat(),
            })

        # Probability
        predicted_date = start_date + timedelta(days=int(months * 30.44))
        if months >= 600:
            probability = 0.0
        elif predicted_date > target_date:
            probability = max(0.0, 1.0 - ((predicted_date - target_date).days / 365.0))
        else:
            probability = min(1.0, 1.0 - max((target_date - predicted_date).days / 365.0, 0))

        return projection, total_contrib, total_interest, months, probability

    def _run_monte_carlo(
        self, target_amount: float, current_amount: float,
        monthly: float, rate: float,
        lump_sum: float | None, lump_sum_date: str | None,
        increase_pct: float, inflation_rate: float,
        income_sources: list[dict], expenses: list[dict],
        start_date: date_type, target_date: date_type,
        num_simulations: int = 500,
    ) -> list[dict] | None:
        all_paths: dict[int, list[float]] = {}
        seed = 42

        for sim_idx in range(num_simulations):
            rng = random.Random(seed + sim_idx)
            # Perturb parameters
            perturbed_monthly = monthly * rng.uniform(0.85, 1.15)
            perturbed_rate = rate * rng.uniform(0.5, 1.5)

            _balance = current_amount
            _months = 0
            _target = target_amount
            monthly_rate_p = perturbed_rate / 100 / 12
            anchor_now = self._current_month_relative(start_date)

            while _balance < _target and _months < 600:
                _months += 1
                _contribution = perturbed_monthly
                if increase_pct > 0 and _months > 1:
                    _contribution *= (1 + increase_pct * ((_months - 1) / 12))

                _income_amount = 0.0
                for src in income_sources:
                    sm = src.get("start_month") or anchor_now
                    em = src.get("end_month")
                    if _is_active(_months, sm, em):
                        _income_amount += _calc_monthly_amount(
                            float(src["amount"]), src["frequency"],
                            src.get("growth_rate"), _months, sm,
                        )

                _expense_amount = 0.0
                for exp in expenses:
                    sm = exp.get("start_month") or anchor_now
                    em = exp.get("end_month")
                    if _is_active(_months, sm, em):
                        _expense_amount += _calc_monthly_amount(
                            float(exp["amount"]), exp["frequency"],
                            exp.get("growth_rate"), _months, sm,
                        )

                _net = _contribution + _income_amount - _expense_amount
                if _net < 0:
                    _net = 0

                _interest = _balance * monthly_rate_p
                _balance = _balance + _net + _interest

                if _months not in all_paths:
                    all_paths[_months] = []
                all_paths[_months].append(_balance)

        if not all_paths:
            return None

        percentiles = []
        max_months = max(all_paths.keys())
        start = 0
        current = 0
        step_size = max(1, max_months // 60)

        for m in range(1, max_months + 1):
            if m not in all_paths:
                continue
            current += 1
            values = sorted(all_paths[m])
            n = len(values)
            p5 = values[int(n * 0.05)]
            p25 = values[int(n * 0.25)]
            p50 = values[int(n * 0.50)]
            p75 = values[int(n * 0.75)]
            p95 = values[int(n * 0.95)]

            if current - start >= step_size or m == max_months:
                percentiles.append({
                    "month": m,
                    "p5": round(p5, 2),
                    "p25": round(p25, 2),
                    "p50": round(p50, 2),
                    "p75": round(p75, 2),
                    "p95": round(p95, 2),
                })
                start = current

        return percentiles

    def _calc_recommendations(
        self, target_amount: float, current_amount: float,
        current_monthly: float, rate: float, inflation_rate: float,
        start_date: date_type, target_date: date_type,
    ) -> list[dict]:
        multipliers = [0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 2.5, 3.0]
        recs = []

        for mult in multipliers:
            contrib = current_monthly * mult
            _, _, _, months, prob = self._run_projection(
                target_amount=target_amount,
                current_amount=current_amount,
                monthly=contrib,
                rate=rate,
                lump_sum=None,
                lump_sum_date=None,
                increase_pct=0,
                inflation_rate=inflation_rate,
                income_sources=[],
                expenses=[],
                start_date=start_date,
                target_date=target_date,
            )
            recs.append({
                "contribution": round(contrib, 2),
                "probability": round(prob, 4),
                "months": months,
            })

        return recs
