"""Analytics repository — all aggregation queries for analytics."""

from __future__ import annotations

import uuid
from datetime import date, timedelta
from decimal import Decimal

import structlog
from sqlalchemy import Date, Float, and_, case, cast, extract, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.models.budget import BudgetModel
from app.infrastructure.models.credit_card import CreditCardModel
from app.infrastructure.models.financial_account import FinancialAccountModel
from app.infrastructure.models.income import IncomeModel
from app.infrastructure.models.loan import LoanModel
from app.infrastructure.models.subscription import SubscriptionModel
from app.infrastructure.models.transaction import TransactionModel

logger = structlog.get_logger()


def _default_month_range() -> tuple[date, date]:
    """Current month start/end."""
    today = date.today()
    start = today.replace(day=1)
    if today.month == 12:
        end = date(today.year + 1, 1, 1) - timedelta(days=1)
    else:
        end = date(today.year, today.month + 1, 1) - timedelta(days=1)
    return start, end


class AnalyticsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ── HELPER: base transaction filter ────────────────────────

    def _tx_filters(self, user_id: uuid.UUID, start: date, end: date) -> list:
        return [
            TransactionModel.user_id == user_id,
            TransactionModel.deleted_at.is_(None),
            TransactionModel.status == "completed",
            TransactionModel.effective_date >= start,
            TransactionModel.effective_date <= end,
        ]

    # ── 1. KPIs ───────────────────────────────────────────────

    async def get_monthly_kpis(self, user_id: uuid.UUID, year: int, month: int) -> dict:
        start = date(year, month, 1)
        if month == 12:
            end = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end = date(year, month + 1, 1) - timedelta(days=1)

        # Total income
        income_stmt = select(func.coalesce(func.sum(TransactionModel.amount), 0)).where(
            and_(
                *self._tx_filters(user_id, start, end),
                TransactionModel.transaction_type == "income",
            )
        )
        total_income = (await self._session.execute(income_stmt)).scalar() or 0

        # Total expenses
        expense_stmt = select(func.coalesce(func.sum(TransactionModel.amount), 0)).where(
            and_(
                *self._tx_filters(user_id, start, end),
                TransactionModel.transaction_type == "expense",
            )
        )
        total_expenses = (await self._session.execute(expense_stmt)).scalar() or 0

        # Transaction count
        count_stmt = select(func.count(TransactionModel.id)).where(
            and_(*self._tx_filters(user_id, start, end))
        )
        tx_count = (await self._session.execute(count_stmt)).scalar() or 0

        # Average transaction
        avg_stmt = select(func.coalesce(func.avg(TransactionModel.amount), 0)).where(
            and_(*self._tx_filters(user_id, start, end))
        )
        avg_tx = (await self._session.execute(avg_stmt)).scalar() or 0

        # Net flow
        net_flow = Decimal(str(total_income)) - Decimal(str(total_expenses))

        # Savings rate
        savings_rate = 0.0
        if float(total_income) > 0:
            savings_rate = round(float(net_flow) / float(total_income) * 100, 2)

        # Previous month for comparison
        prev_start = date(year, month, 1) - timedelta(days=1)
        prev_start = prev_start.replace(day=1)
        if month == 1:
            prev_start = date(year - 1, 12, 1)
        prev_end = date(year, month, 1) - timedelta(days=1)

        prev_income_stmt = select(func.coalesce(func.sum(TransactionModel.amount), 0)).where(
            and_(
                *self._tx_filters(user_id, prev_start, prev_end),
                TransactionModel.transaction_type == "income",
            )
        )
        prev_income = (await self._session.execute(prev_income_stmt)).scalar() or 0

        prev_expense_stmt = select(func.coalesce(func.sum(TransactionModel.amount), 0)).where(
            and_(
                *self._tx_filters(user_id, prev_start, prev_end),
                TransactionModel.transaction_type == "expense",
            )
        )
        prev_expenses = (await self._session.execute(prev_expense_stmt)).scalar() or 0

        # Income change %
        income_change_pct = 0.0
        if float(prev_income) > 0:
            income_change_pct = round(
                (float(total_income) - float(prev_income)) / float(prev_income) * 100, 2
            )

        # Expense change %
        expense_change_pct = 0.0
        if float(prev_expenses) > 0:
            expense_change_pct = round(
                (float(total_expenses) - float(prev_expenses)) / float(prev_expenses) * 100, 2
            )

        return {
            "period": {
                "year": year,
                "month": month,
                "start": start.isoformat(),
                "end": end.isoformat(),
            },
            "total_income": float(total_income),
            "total_expenses": float(total_expenses),
            "net_flow": float(net_flow),
            "savings_rate": savings_rate,
            "transaction_count": tx_count,
            "average_transaction": round(float(avg_tx), 2),
            "comparison": {
                "prev_income": float(prev_income),
                "prev_expenses": float(prev_expenses),
                "income_change_pct": income_change_pct,
                "expense_change_pct": expense_change_pct,
            },
        }

    async def get_portfolio_kpis(self, user_id: uuid.UUID) -> dict:
        """Overall portfolio KPIs across all time."""
        # Net worth
        nw_stmt = select(func.coalesce(func.sum(FinancialAccountModel.balance), 0)).where(
            FinancialAccountModel.user_id == user_id,
            FinancialAccountModel.deleted_at.is_(None),
            FinancialAccountModel.include_in_net_worth == True,  # noqa: E712
            FinancialAccountModel.status == "active",
        )
        net_worth = (await self._session.execute(nw_stmt)).scalar() or 0

        # Total debt
        debt_stmt = select(func.coalesce(func.sum(LoanModel.current_balance), 0)).where(
            LoanModel.user_id == user_id,
            LoanModel.deleted_at.is_(None),
            LoanModel.status.in_(["active", "pending"]),
        )
        total_debt = (await self._session.execute(debt_stmt)).scalar() or 0

        # Total monthly loan payments
        loan_pmt_stmt = select(func.coalesce(func.sum(LoanModel.monthly_payment), 0)).where(
            LoanModel.user_id == user_id,
            LoanModel.deleted_at.is_(None),
            LoanModel.status.in_(["active", "pending"]),
        )
        total_monthly_debt = (await self._session.execute(loan_pmt_stmt)).scalar() or 0

        # Monthly income (last 3 months average)
        three_months_ago = date.today() - timedelta(days=90)
        avg_income_stmt = select(func.coalesce(func.sum(TransactionModel.amount) / 3, 0)).where(
            TransactionModel.user_id == user_id,
            TransactionModel.deleted_at.is_(None),
            TransactionModel.status == "completed",
            TransactionModel.transaction_type == "income",
            TransactionModel.effective_date >= three_months_ago,
        )
        avg_monthly_income = (await self._session.execute(avg_income_stmt)).scalar() or 0

        # Debt-to-income
        dti = 0.0
        if float(avg_monthly_income) > 0:
            dti = round(float(total_monthly_debt) / float(avg_monthly_income) * 100, 2)

        # Net worth (assets - liabilities)
        net_worth_value = float(net_worth) - float(total_debt)

        # Active budgets count
        budget_stmt = select(func.count(BudgetModel.id)).where(
            BudgetModel.user_id == user_id,
            BudgetModel.deleted_at.is_(None),
            BudgetModel.is_active == True,  # noqa: E712
        )
        active_budgets = (await self._session.execute(budget_stmt)).scalar() or 0

        # Active goals count
        from app.infrastructure.models.financial_goal import FinancialGoalModel

        goal_stmt = select(func.count(FinancialGoalModel.id)).where(
            FinancialGoalModel.user_id == user_id,
            FinancialGoalModel.deleted_at.is_(None),
            FinancialGoalModel.status == "active",
        )
        active_goals = (await self._session.execute(goal_stmt)).scalar() or 0

        # Active loans count
        loan_count_stmt = select(func.count(LoanModel.id)).where(
            LoanModel.user_id == user_id,
            LoanModel.deleted_at.is_(None),
            LoanModel.status.in_(["active", "pending"]),
        )
        active_loans = (await self._session.execute(loan_count_stmt)).scalar() or 0

        return {
            "net_worth": net_worth_value,
            "total_assets": float(net_worth),
            "total_liabilities": float(total_debt),
            "debt_to_income": dti,
            "total_monthly_debt_payments": float(total_monthly_debt),
            "avg_monthly_income": round(float(avg_monthly_income), 2),
            "active_budgets": active_budgets,
            "active_goals": active_goals,
            "active_loans": active_loans,
        }

    # ── 2. TRENDS ──────────────────────────────────────────────

    async def get_spending_trend(
        self, user_id: uuid.UUID, start: date, end: date, period: str = "monthly"
    ) -> dict:
        if period == "monthly":
            group_expr = func.date_trunc("month", TransactionModel.effective_date)
            label = "month"
        elif period == "weekly":
            group_expr = func.date_trunc("week", TransactionModel.effective_date)
            label = "week"
        else:  # daily
            group_expr = TransactionModel.effective_date
            label = "day"

        stmt = (
            select(
                group_expr.label(label),
                func.coalesce(func.sum(TransactionModel.amount), 0).label("total"),
                func.count(TransactionModel.id).label("count"),
            )
            .where(
                and_(
                    *self._tx_filters(user_id, start, end),
                    TransactionModel.transaction_type == "expense",
                )
            )
            .group_by(label)
            .order_by(label)
        )

        result = await self._session.execute(stmt)
        rows = result.all()

        items = [
            {
                "period": str(getattr(r, label))[:10]
                if hasattr(getattr(r, label), "isoformat")
                else str(getattr(r, label)),
                "total": float(r.total),
                "count": r.count,
            }
            for r in rows
        ]

        totals = [i["total"] for i in items]
        avg = sum(totals) / len(totals) if totals else 0
        max_val = max(totals) if totals else 0
        min_val = min(totals) if totals else 0

        return {
            "period": period,
            "start": start.isoformat(),
            "end": end.isoformat(),
            "data": items,
            "summary": {
                "total_spent": sum(totals),
                "average": round(avg, 2),
                "max": max_val,
                "min": min_val,
                "periods": len(items),
            },
        }

    async def get_income_trend(
        self, user_id: uuid.UUID, start: date, end: date, period: str = "monthly"
    ) -> dict:
        if period == "monthly":
            group_expr = func.date_trunc("month", TransactionModel.effective_date)
            label = "month"
        elif period == "weekly":
            group_expr = func.date_trunc("week", TransactionModel.effective_date)
            label = "week"
        else:
            group_expr = TransactionModel.effective_date
            label = "day"

        stmt = (
            select(
                group_expr.label(label),
                func.coalesce(func.sum(TransactionModel.amount), 0).label("total"),
                func.count(TransactionModel.id).label("count"),
            )
            .where(
                and_(
                    *self._tx_filters(user_id, start, end),
                    TransactionModel.transaction_type == "income",
                )
            )
            .group_by(label)
            .order_by(label)
        )

        result = await self._session.execute(stmt)
        rows = result.all()

        items = [
            {
                "period": str(getattr(r, label))[:10]
                if hasattr(getattr(r, label), "isoformat")
                else str(getattr(r, label)),
                "total": float(r.total),
                "count": r.count,
            }
            for r in rows
        ]

        totals = [i["total"] for i in items]
        avg = sum(totals) / len(totals) if totals else 0

        return {
            "period": period,
            "start": start.isoformat(),
            "end": end.isoformat(),
            "data": items,
            "summary": {
                "total_income": sum(totals),
                "average": round(avg, 2),
                "periods": len(items),
            },
        }

    async def get_category_breakdown(
        self,
        user_id: uuid.UUID,
        start: date,
        end: date,
        transaction_type: str = "expense",
    ) -> dict:
        from app.infrastructure.models.category import CategoryModel

        stmt = (
            select(
                CategoryModel.name.label("category_name"),
                CategoryModel.icon.label("category_icon"),
                CategoryModel.color.label("category_color"),
                func.coalesce(func.sum(TransactionModel.amount), 0).label("total"),
                func.count(TransactionModel.id).label("count"),
            )
            .join(CategoryModel, TransactionModel.category_id == CategoryModel.id, isouter=True)
            .where(
                and_(
                    *self._tx_filters(user_id, start, end),
                    TransactionModel.transaction_type == transaction_type,
                )
            )
            .group_by(CategoryModel.name, CategoryModel.icon, CategoryModel.color)
            .order_by(func.sum(TransactionModel.amount).desc())
        )

        result = await self._session.execute(stmt)
        rows = result.all()

        grand_total = sum(float(r.total) for r in rows)
        items = []
        for r in rows:
            pct = round(float(r.total) / grand_total * 100, 2) if grand_total > 0 else 0
            items.append(
                {
                    "category": r.category_name or "Sin categoría",
                    "icon": r.category_icon,
                    "color": r.category_color,
                    "total": float(r.total),
                    "count": r.count,
                    "percentage": pct,
                }
            )

        return {
            "transaction_type": transaction_type,
            "start": start.isoformat(),
            "end": end.isoformat(),
            "grand_total": grand_total,
            "categories": items,
        }

    async def get_top_categories(
        self,
        user_id: uuid.UUID,
        start: date,
        end: date,
        limit: int = 5,
        transaction_type: str = "expense",
    ) -> dict:
        breakdown = await self.get_category_breakdown(user_id, start, end, transaction_type)
        return {
            "transaction_type": transaction_type,
            "start": start.isoformat(),
            "end": end.isoformat(),
            "top_categories": breakdown["categories"][:limit],
        }

    # ── 3. CASH FLOW ──────────────────────────────────────────

    async def get_cash_flow(self, user_id: uuid.UUID, start: date, end: date) -> dict:
        stmt = (
            select(
                func.date_trunc("month", TransactionModel.effective_date).label("month"),
                func.coalesce(
                    func.sum(
                        case(
                            (
                                TransactionModel.transaction_type == "income",
                                TransactionModel.amount,
                            ),
                            else_=0,
                        )
                    ),
                    0,
                ).label("income"),
                func.coalesce(
                    func.sum(
                        case(
                            (
                                TransactionModel.transaction_type == "expense",
                                TransactionModel.amount,
                            ),
                            else_=0,
                        )
                    ),
                    0,
                ).label("expenses"),
            )
            .where(
                and_(
                    *self._tx_filters(user_id, start, end),
                    TransactionModel.transaction_type.in_(["income", "expense"]),
                )
            )
            .group_by("month")
            .order_by("month")
        )

        result = await self._session.execute(stmt)
        rows = result.all()

        items = []
        for r in rows:
            cf = float(r.income) - float(r.expenses)
            items.append(
                {
                    "month": str(r.month)[:10],
                    "income": float(r.income),
                    "expenses": float(r.expenses),
                    "net_flow": cf,
                    "is_positive": cf >= 0,
                }
            )

        total_income = sum(i["income"] for i in items)
        total_expenses = sum(i["expenses"] for i in items)

        return {
            "start": start.isoformat(),
            "end": end.isoformat(),
            "data": items,
            "summary": {
                "total_income": total_income,
                "total_expenses": total_expenses,
                "net_flow": total_income - total_expenses,
                "months": len(items),
                "positive_months": sum(1 for i in items if i["is_positive"]),
                "negative_months": sum(1 for i in items if not i["is_positive"]),
            },
        }

    async def get_cash_flow_by_account(self, user_id: uuid.UUID, start: date, end: date) -> dict:
        stmt = (
            select(
                FinancialAccountModel.name.label("account_name"),
                FinancialAccountModel.account_type.label("account_type"),
                func.coalesce(
                    func.sum(
                        case(
                            (
                                TransactionModel.transaction_type == "income",
                                TransactionModel.amount,
                            ),
                            else_=0,
                        )
                    ),
                    0,
                ).label("income"),
                func.coalesce(
                    func.sum(
                        case(
                            (
                                TransactionModel.transaction_type == "expense",
                                TransactionModel.amount,
                            ),
                            else_=0,
                        )
                    ),
                    0,
                ).label("expenses"),
            )
            .join(
                FinancialAccountModel,
                TransactionModel.account_id == FinancialAccountModel.id,
            )
            .where(
                and_(
                    *self._tx_filters(user_id, start, end),
                    TransactionModel.transaction_type.in_(["income", "expense"]),
                )
            )
            .group_by(FinancialAccountModel.name, FinancialAccountModel.account_type)
            .order_by(func.sum(TransactionModel.amount).desc())
        )

        result = await self._session.execute(stmt)
        rows = result.all()

        items = [
            {
                "account": r.account_name,
                "account_type": r.account_type,
                "income": float(r.income),
                "expenses": float(r.expenses),
                "net_flow": float(r.income) - float(r.expenses),
            }
            for r in rows
        ]

        return {
            "start": start.isoformat(),
            "end": end.isoformat(),
            "accounts": items,
        }

    # ── 4. NET WORTH ──────────────────────────────────────────

    async def get_net_worth(self, user_id: uuid.UUID) -> dict:
        # Assets (active accounts)
        asset_stmt = (
            select(
                FinancialAccountModel.name,
                FinancialAccountModel.account_type,
                FinancialAccountModel.balance,
                FinancialAccountModel.currency_code,
            )
            .where(
                FinancialAccountModel.user_id == user_id,
                FinancialAccountModel.deleted_at.is_(None),
                FinancialAccountModel.include_in_net_worth == True,  # noqa: E712
                FinancialAccountModel.status == "active",
            )
            .order_by(FinancialAccountModel.balance.desc())
        )

        result = await self._session.execute(asset_stmt)
        accounts = result.all()

        total_assets = sum(float(a.balance) for a in accounts)
        assets_by_type = {}
        for a in accounts:
            t = a.account_type
            if t not in assets_by_type:
                assets_by_type[t] = {"total": 0, "accounts": []}
            assets_by_type[t]["total"] += float(a.balance)
            assets_by_type[t]["accounts"].append(
                {
                    "name": a.name,
                    "balance": float(a.balance),
                    "currency": a.currency_code,
                }
            )

        # Liabilities (active loans)
        debt_stmt = (
            select(
                LoanModel.name,
                LoanModel.loan_type,
                LoanModel.current_balance,
                LoanModel.monthly_payment,
            )
            .where(
                LoanModel.user_id == user_id,
                LoanModel.deleted_at.is_(None),
                LoanModel.status.in_(["active", "pending"]),
            )
            .order_by(LoanModel.current_balance.desc())
        )

        debt_result = await self._session.execute(debt_stmt)
        loans = debt_result.all()

        total_liabilities = sum(float(l.current_balance) for l in loans)
        liabilities_by_type = {}
        for l in loans:
            t = l.loan_type
            if t not in liabilities_by_type:
                liabilities_by_type[t] = {"total": 0, "loans": []}
            liabilities_by_type[t]["total"] += float(l.current_balance)
            liabilities_by_type[t]["loans"].append(
                {
                    "name": l.name,
                    "balance": float(l.current_balance),
                    "monthly_payment": float(l.monthly_payment),
                }
            )

        # Credit card debt (utilized credit)
        cc_stmt = select(
            func.coalesce(
                func.sum(CreditCardModel.credit_limit - CreditCardModel.available_credit), 0
            )
        ).where(
            CreditCardModel.user_id == user_id,
            CreditCardModel.deleted_at.is_(None),
            CreditCardModel.is_active == True,  # noqa: E712
        )
        cc_debt = (await self._session.execute(cc_stmt)).scalar() or 0
        total_liabilities += float(cc_debt)

        net_worth = total_assets - total_liabilities

        return {
            "net_worth": round(net_worth, 2),
            "total_assets": round(total_assets, 2),
            "total_liabilities": round(total_liabilities, 2),
            "credit_card_debt": round(float(cc_debt), 2),
            "assets_by_type": assets_by_type,
            "liabilities_by_type": liabilities_by_type,
        }

    # ── 5. HEATMAPS ───────────────────────────────────────────

    async def get_spending_heatmap(
        self,
        user_id: uuid.UUID,
        start: date,
        end: date,
        granularity: str = "day_of_week_month",
    ) -> dict:
        if granularity == "day_of_week_month":
            stmt = (
                select(
                    extract("dow", TransactionModel.effective_date).label("day_of_week"),
                    extract("month", TransactionModel.effective_date).label("month"),
                    func.coalesce(func.sum(TransactionModel.amount), 0).label("total"),
                )
                .where(
                    and_(
                        *self._tx_filters(user_id, start, end),
                        TransactionModel.transaction_type == "expense",
                    )
                )
                .group_by("day_of_week", "month")
                .order_by("month", "day_of_week")
            )

            result = await self._session.execute(stmt)
            rows = result.all()

            # Build matrix: day_of_week (0=Sun..6=Sat) x month (1-12)
            DAYS = ["Dom", "Lun", "Mar", "Mié", "Jue", "Vie", "Sáb"]
            MONTHS = [
                "",
                "Ene",
                "Feb",
                "Mar",
                "Abr",
                "May",
                "Jun",
                "Jul",
                "Ago",
                "Sep",
                "Oct",
                "Nov",
                "Dic",
            ]

            matrix = {}
            for r in rows:
                dow = int(r.day_of_week)
                m = int(r.month)
                key = f"{dow}-{m}"
                matrix[key] = float(r.total)

            data = []
            for dow in range(7):
                for m in range(1, 13):
                    data.append(
                        {
                            "day_of_week": dow,
                            "day_name": DAYS[dow],
                            "month": m,
                            "month_name": MONTHS[m],
                            "total": matrix.get(f"{dow}-{m}", 0),
                        }
                    )

            max_val = max((d["total"] for d in data), default=0)

            return {
                "granularity": granularity,
                "start": start.isoformat(),
                "end": end.isoformat(),
                "data": data,
                "max_value": max_val,
                "days": DAYS,
                "months": [MONTHS[m] for m in range(1, 13)],
            }

        elif granularity == "category_month":
            from app.infrastructure.models.category import CategoryModel

            stmt = (
                select(
                    CategoryModel.name.label("category"),
                    extract("month", TransactionModel.effective_date).label("month"),
                    func.coalesce(func.sum(TransactionModel.amount), 0).label("total"),
                )
                .join(CategoryModel, TransactionModel.category_id == CategoryModel.id, isouter=True)
                .where(
                    and_(
                        *self._tx_filters(user_id, start, end),
                        TransactionModel.transaction_type == "expense",
                    )
                )
                .group_by("category", "month")
                .order_by("month")
            )

            result = await self._session.execute(stmt)
            rows = result.all()

            MONTHS = [
                "",
                "Ene",
                "Feb",
                "Mar",
                "Abr",
                "May",
                "Jun",
                "Jul",
                "Ago",
                "Sep",
                "Oct",
                "Nov",
                "Dic",
            ]

            categories = list({r.category or "Sin categoría" for r in rows})
            matrix = {}
            for r in rows:
                cat = r.category or "Sin categoría"
                m = int(r.month)
                matrix[f"{cat}-{m}"] = float(r.total)

            data = []
            for cat in categories:
                for m in range(1, 13):
                    data.append(
                        {
                            "category": cat,
                            "month": m,
                            "month_name": MONTHS[m],
                            "total": matrix.get(f"{cat}-{m}", 0),
                        }
                    )

            max_val = max((d["total"] for d in data), default=0)

            return {
                "granularity": granularity,
                "start": start.isoformat(),
                "end": end.isoformat(),
                "data": data,
                "max_value": max_val,
                "categories": categories,
                "months": [MONTHS[m] for m in range(1, 13)],
            }

        else:  # day_of_week_hour (default)
            stmt = (
                select(
                    extract("dow", TransactionModel.effective_date).label("day_of_week"),
                    func.coalesce(func.sum(TransactionModel.amount), 0).label("total"),
                )
                .where(
                    and_(
                        *self._tx_filters(user_id, start, end),
                        TransactionModel.transaction_type == "expense",
                    )
                )
                .group_by("day_of_week")
                .order_by("day_of_week")
            )

            result = await self._session.execute(stmt)
            rows = result.all()

            DAYS = ["Dom", "Lun", "Mar", "Mié", "Jue", "Vie", "Sáb"]
            by_day = {int(r.day_of_week): float(r.total) for r in rows}

            data = [
                {"day_of_week": d, "day_name": DAYS[d], "total": by_day.get(d, 0)} for d in range(7)
            ]

            return {
                "granularity": "day_of_week",
                "start": start.isoformat(),
                "end": end.isoformat(),
                "data": data,
                "max_value": max((d["total"] for d in data), default=0),
                "days": DAYS,
            }

    # ── 6. DASHBOARD ───────────────────────────────────────────

    async def get_dashboard(self, user_id: uuid.UUID) -> dict:
        today = date.today()
        month_start = today.replace(day=1)
        if today.month == 12:
            month_end = date(today.year + 1, 1, 1) - timedelta(days=1)
        else:
            month_end = date(today.year, today.month + 1, 1) - timedelta(days=1)

        # KPIs
        kpis = await self.get_monthly_kpis(user_id, today.year, today.month)

        # Net worth
        net_worth = await self.get_net_worth(user_id)

        # Portfolio KPIs
        portfolio = await self.get_portfolio_kpis(user_id)

        # Current month cash flow
        cash_flow = await self.get_cash_flow(user_id, month_start, month_end)

        # Top 5 spending categories (current month)
        top_cats = await self.get_top_categories(user_id, month_start, month_end, limit=5)

        # Spending trend (last 6 months)
        six_months_ago = today - timedelta(days=180)
        spending_trend = await self.get_spending_trend(user_id, six_months_ago, today, "monthly")

        # Upcoming loan payments
        from app.infrastructure.models.loan import LoanModel

        upcoming_stmt = (
            select(
                LoanModel.name,
                LoanModel.monthly_payment,
                LoanModel.next_payment_date,
            )
            .where(
                LoanModel.user_id == user_id,
                LoanModel.deleted_at.is_(None),
                LoanModel.status == "active",
                LoanModel.next_payment_date.isnot(None),
                LoanModel.next_payment_date <= today + timedelta(days=30),
            )
            .order_by(LoanModel.next_payment_date)
        )
        upcoming_result = await self._session.execute(upcoming_stmt)
        upcoming_loans = [
            {
                "name": r.name,
                "payment": float(r.monthly_payment),
                "due_date": r.next_payment_date.isoformat() if r.next_payment_date else None,
            }
            for r in upcoming_result.all()
        ]

        # Active goals progress
        from app.infrastructure.models.financial_goal import FinancialGoalModel

        goals_stmt = (
            select(
                FinancialGoalModel.name,
                FinancialGoalModel.target_amount,
                FinancialGoalModel.current_amount,
                FinancialGoalModel.target_date,
            )
            .where(
                FinancialGoalModel.user_id == user_id,
                FinancialGoalModel.deleted_at.is_(None),
                FinancialGoalModel.status == "active",
            )
            .order_by(FinancialGoalModel.target_date)
        )
        goals_result = await self._session.execute(goals_stmt)
        goals = []
        for r in goals_result.all():
            pct = 0.0
            if float(r.target_amount) > 0:
                pct = round(float(r.current_amount) / float(r.target_amount) * 100, 2)
            goals.append(
                {
                    "name": r.name,
                    "target": float(r.target_amount),
                    "current": float(r.current_amount),
                    "progress_pct": pct,
                    "target_date": r.target_date.isoformat() if r.target_date else None,
                }
            )

        return {
            "kpis": kpis,
            "net_worth": net_worth,
            "portfolio": portfolio,
            "cash_flow": cash_flow,
            "top_categories": top_cats,
            "spending_trend": spending_trend,
            "upcoming_payments": upcoming_loans,
            "goals": goals,
        }
