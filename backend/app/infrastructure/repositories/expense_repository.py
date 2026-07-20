"""Repository for expense module persistence."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog
from sqlalchemy import and_, func, select

from app.infrastructure.models.category import CategoryModel
from app.infrastructure.models.credit_card import CreditCardModel
from app.infrastructure.models.credit_card_bill import CreditCardBillModel
from app.infrastructure.models.expense_service import ExpenseServiceModel
from app.infrastructure.models.expense_template import ExpenseTemplateModel
from app.infrastructure.models.subscription import SubscriptionModel
from app.infrastructure.models.transaction import TransactionModel

if TYPE_CHECKING:
    import uuid
    from datetime import date  # noqa: TC004
    from decimal import Decimal  # noqa: F401

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class ExpenseRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ==============================================================
    # Expense Dashboard / Analytics
    # ==============================================================

    async def get_expense_dashboard(
        self, user_id: uuid.UUID, date_from: date, date_to: date
    ) -> dict:
        from decimal import Decimal

        base_filter = and_(
            TransactionModel.user_id == user_id,
            TransactionModel.deleted_at.is_(None),
            TransactionModel.transaction_type == "expense",
            TransactionModel.effective_date >= date_from,
            TransactionModel.effective_date <= date_to,
        )

        # Total expenses
        total_stmt = select(
            func.count(TransactionModel.id).label("count"),
            func.sum(TransactionModel.amount).label("total"),
        ).where(base_filter)
        result = await self._session.execute(total_stmt)
        row = result.one()
        total_amount = Decimal(str(row.total or 0))
        total_count = row.count or 0

        # By category
        cat_stmt = (
            select(
                CategoryModel.name,
                func.count(TransactionModel.id).label("count"),
                func.sum(TransactionModel.amount).label("total"),
            )
            .join(TransactionModel, TransactionModel.category_id == CategoryModel.id)
            .where(base_filter)
            .group_by(CategoryModel.name)
            .order_by(func.sum(TransactionModel.amount).desc())
        )
        cat_result = await self._session.execute(cat_stmt)
        by_category = [
            {
                "category": r.name,
                "count": r.count,
                "total": str(r.total or 0),
                "percentage": str(round((float(r.total or 0) / float(total_amount) * 100), 2))
                if total_amount > 0
                else "0",
            }
            for r in cat_result.all()
        ]

        # Daily trend
        daily_stmt = (
            select(
                TransactionModel.effective_date,
                func.count(TransactionModel.id).label("count"),
                func.sum(TransactionModel.amount).label("total"),
            )
            .where(base_filter)
            .group_by(TransactionModel.effective_date)
            .order_by(TransactionModel.effective_date.asc())
        )
        daily_result = await self._session.execute(daily_stmt)
        daily_trend = [
            {"date": r.effective_date.isoformat(), "count": r.count, "total": str(r.total or 0)}
            for r in daily_result.all()
        ]

        # Active subscriptions total
        sub_stmt = select(func.sum(SubscriptionModel.amount)).where(
            SubscriptionModel.user_id == user_id,
            SubscriptionModel.status == "active",
            SubscriptionModel.deleted_at.is_(None),
        )
        sub_result = await self._session.execute(sub_stmt)
        monthly_subscriptions = Decimal(str(sub_result.scalar() or 0))

        return {
            "period_start": date_from.isoformat(),
            "period_end": date_to.isoformat(),
            "total_expenses": str(total_amount),
            "total_count": total_count,
            "daily_average": str(
                round(float(total_amount) / max(1, (date_to - date_from).days + 1), 2)
            ),
            "monthly_subscriptions": str(monthly_subscriptions),
            "by_category": by_category,
            "daily_trend": daily_trend,
        }

    async def detect_duplicates(self, user_id: uuid.UUID, days: int = 30) -> list[dict]:
        from datetime import date, timedelta

        today = date.today()  # noqa: DTZ011
        cutoff = today - timedelta(days=days)

        stmt = (
            select(TransactionModel)
            .where(
                TransactionModel.user_id == user_id,
                TransactionModel.deleted_at.is_(None),
                TransactionModel.transaction_type == "expense",
                TransactionModel.effective_date >= cutoff,
            )
            .order_by(TransactionModel.amount.asc(), TransactionModel.effective_date.asc())
        )
        result = await self._session.execute(stmt)
        txs = list(result.scalars().all())

        # Find duplicates: same amount within 1 day
        duplicates: list[dict] = []
        seen: dict[str, list] = {}
        for tx in txs:
            key = f"{tx.amount}_{tx.effective_date}"
            if key not in seen:
                seen[key] = []
            seen[key].append(tx)

        for key, group in seen.items():  # noqa: B007
            if len(group) > 1:
                duplicates.append(
                    {
                        "transactions": [
                            {
                                "id": str(tx.id),
                                "description": tx.description,
                                "amount": str(tx.amount),
                                "date": tx.effective_date.isoformat(),
                                "account_id": str(tx.account_id),
                            }
                            for tx in group
                        ],
                        "amount": str(group[0].amount),
                        "count": len(group),
                    }
                )

        return duplicates

    async def detect_recurring_candidates(self, user_id: uuid.UUID) -> list[dict]:
        """Find expense transactions that repeat with similar amounts (potential recurring expenses)."""
        from collections import defaultdict
        from datetime import date as date_type
        from datetime import timedelta

        today = date_type.today()  # noqa: DTZ011
        cutoff = today - timedelta(days=180)  # 6 months lookback

        stmt = (
            select(TransactionModel)
            .where(
                TransactionModel.user_id == user_id,
                TransactionModel.deleted_at.is_(None),
                TransactionModel.transaction_type == "expense",
                TransactionModel.effective_date >= cutoff,
            )
            .order_by(TransactionModel.description.asc())
        )
        result = await self._session.execute(stmt)
        txs = list(result.scalars().all())

        # Group by similar description + amount
        groups: dict[str, list] = defaultdict(list)
        for tx in txs:
            # Normalize: lowercase, strip, first 20 chars
            norm_desc = (tx.description or "").lower().strip()[:20]
            key = f"{norm_desc}_{tx.amount}"
            groups[key].append(tx)

        candidates: list[dict] = []
        for key, group in groups.items():  # noqa: B007
            if len(group) >= 3:  # at least 3 occurrences
                dates = sorted([tx.effective_date for tx in group])
                # Check if dates are roughly monthly
                gaps = [(dates[i + 1] - dates[i]).days for i in range(len(dates) - 1)]
                avg_gap = sum(gaps) / len(gaps) if gaps else 0
                is_monthly_like = 25 <= avg_gap <= 35  # within 25-35 days

                candidates.append(
                    {
                        "description": group[0].description,
                        "amount": str(group[0].amount),
                        "occurrences": len(group),
                        "avg_frequency_days": round(avg_gap, 1),
                        "is_monthly_like": is_monthly_like,
                        "first_date": dates[0].isoformat(),
                        "last_date": dates[-1].isoformat(),
                        "sample_transaction_id": str(group[0].id),
                    }
                )

        # Sort by occurrences descending
        candidates.sort(key=lambda x: x["occurrences"], reverse=True)
        return candidates

    # ==============================================================
    # Spending Patterns
    # ==============================================================

    async def get_spending_patterns(self, user_id: uuid.UUID) -> dict:
        # Top spending categories (last 3 months)
        from datetime import date as date_type
        from datetime import timedelta
        from decimal import Decimal

        today = date_type.today()  # noqa: DTZ011
        three_months_ago = today - timedelta(days=90)

        cat_stmt = (
            select(
                CategoryModel.name,
                CategoryModel.icon,
                func.sum(TransactionModel.amount).label("total"),
                func.count(TransactionModel.id).label("count"),
            )
            .join(TransactionModel, TransactionModel.category_id == CategoryModel.id)
            .where(
                TransactionModel.user_id == user_id,
                TransactionModel.deleted_at.is_(None),
                TransactionModel.transaction_type == "expense",
                TransactionModel.effective_date >= three_months_ago,
            )
            .group_by(CategoryModel.name, CategoryModel.icon)
            .order_by(func.sum(TransactionModel.amount).desc())
            .limit(10)
        )
        cat_result = await self._session.execute(cat_stmt)
        top_categories = [
            {"category": r.name, "icon": r.icon, "total": str(r.total or 0), "count": r.count}
            for r in cat_result.all()
        ]

        # Monthly average
        monthly_stmt = (
            select(
                func.extract("month", TransactionModel.effective_date).label("month"),
                func.extract("year", TransactionModel.effective_date).label("year"),
                func.sum(TransactionModel.amount).label("total"),
            )
            .where(
                TransactionModel.user_id == user_id,
                TransactionModel.deleted_at.is_(None),
                TransactionModel.transaction_type == "expense",
                TransactionModel.effective_date >= three_months_ago,
            )
            .group_by(
                func.extract("month", TransactionModel.effective_date),
                func.extract("year", TransactionModel.effective_date),
            )
        )
        monthly_result = await self._session.execute(monthly_stmt)
        monthly_data = [
            {"year": int(r.year), "month": int(r.month), "total": str(r.total or 0)}
            for r in monthly_result.all()
        ]

        avg_monthly = Decimal("0")
        if monthly_data:
            totals = [Decimal(m["total"]) for m in monthly_data]
            avg_monthly = sum(totals) / len(totals)

        return {
            "top_categories": top_categories,
            "monthly_data": monthly_data,
            "average_monthly_expense": str(round(float(avg_monthly), 2)),
            "period": f"{three_months_ago.isoformat()} to {today.isoformat()}",
        }

    # ==============================================================
    # Templates CRUD
    # ==============================================================

    async def create_template(self, user_id: uuid.UUID, **kwargs: object) -> ExpenseTemplateModel:
        template = ExpenseTemplateModel(user_id=user_id, **kwargs)  # type: ignore[arg-type]
        self._session.add(template)
        await self._session.flush()
        logger.info(
            "template_created",
            user_id=str(user_id),
            template_id=str(template.id),
            name=template.name,
        )
        return template

    async def get_template_by_id(
        self, template_id: uuid.UUID, user_id: uuid.UUID
    ) -> ExpenseTemplateModel | None:
        stmt = select(ExpenseTemplateModel).where(
            ExpenseTemplateModel.id == template_id,
            ExpenseTemplateModel.user_id == user_id,
            ExpenseTemplateModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_templates(self, user_id: uuid.UUID) -> list[ExpenseTemplateModel]:
        stmt = (
            select(ExpenseTemplateModel)
            .where(
                ExpenseTemplateModel.user_id == user_id,
                ExpenseTemplateModel.deleted_at.is_(None),
            )
            .order_by(ExpenseTemplateModel.sort_order.asc(), ExpenseTemplateModel.name.asc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def delete_template(self, template_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        from datetime import UTC, datetime

        template = await self.get_template_by_id(template_id, user_id)
        if template is None:
            return False
        template.deleted_at = datetime.now(UTC)
        await self._session.flush()
        return True

    async def increment_template_usage(self, template_id: uuid.UUID) -> None:
        from datetime import UTC, datetime

        template = await self._session.get(ExpenseTemplateModel, template_id)
        if template:
            template.usage_count += 1
            template.last_used_at = datetime.now(UTC)
            await self._session.flush()

    # ==============================================================
    # Services CRUD
    # ==============================================================

    async def create_service(self, user_id: uuid.UUID, **kwargs: object) -> ExpenseServiceModel:
        service = ExpenseServiceModel(user_id=user_id, **kwargs)  # type: ignore[arg-type]
        self._session.add(service)
        await self._session.flush()
        logger.info(
            "service_created", user_id=str(user_id), service_id=str(service.id), name=service.name
        )
        return service

    async def get_service_by_id(
        self, service_id: uuid.UUID, user_id: uuid.UUID
    ) -> ExpenseServiceModel | None:
        stmt = select(ExpenseServiceModel).where(
            ExpenseServiceModel.id == service_id,
            ExpenseServiceModel.user_id == user_id,
            ExpenseServiceModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_services(
        self, user_id: uuid.UUID, *, is_active: bool | None = None, service_type: str | None = None
    ) -> list[ExpenseServiceModel]:
        stmt = select(ExpenseServiceModel).where(
            ExpenseServiceModel.user_id == user_id,
            ExpenseServiceModel.deleted_at.is_(None),
        )
        if is_active is not None:
            stmt = stmt.where(ExpenseServiceModel.is_active == is_active)
        if service_type:
            stmt = stmt.where(ExpenseServiceModel.service_type == service_type)
        stmt = stmt.order_by(ExpenseServiceModel.name.asc())
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update_service(
        self, service_id: uuid.UUID, user_id: uuid.UUID, **kwargs: object
    ) -> ExpenseServiceModel | None:
        service = await self.get_service_by_id(service_id, user_id)
        if service is None:
            return None
        for key, value in kwargs.items():
            if hasattr(service, key):
                setattr(service, key, value)
        await self._session.flush()
        await self._session.refresh(service)
        return service

    async def delete_service(self, service_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        from datetime import UTC, datetime

        service = await self.get_service_by_id(service_id, user_id)
        if service is None:
            return False
        service.deleted_at = datetime.now(UTC)
        await self._session.flush()
        return True

    async def list_upcoming_services(
        self, user_id: uuid.UUID, days_ahead: int = 30
    ) -> list[ExpenseServiceModel]:
        from datetime import date as date_type
        from datetime import timedelta

        today = date_type.today()  # noqa: DTZ011
        cutoff = today + timedelta(days=days_ahead)
        stmt = select(ExpenseServiceModel).where(
            ExpenseServiceModel.user_id == user_id,
            ExpenseServiceModel.is_active.is_(True),
            ExpenseServiceModel.deleted_at.is_(None),
            ExpenseServiceModel.due_day.isnot(None),
        )
        result = await self._session.execute(stmt)
        services = list(result.scalars().all())
        # Filter by due day in the next N days
        upcoming = []
        for s in services:
            if s.due_day and s.due_day <= cutoff.day:
                upcoming.append(s)
        return upcoming

    # ==============================================================
    # Subscriptions CRUD
    # ==============================================================

    async def create_subscription(self, user_id: uuid.UUID, **kwargs: object) -> SubscriptionModel:
        sub = SubscriptionModel(user_id=user_id, **kwargs)  # type: ignore[arg-type]
        self._session.add(sub)
        await self._session.flush()
        logger.info("subscription_created", user_id=str(user_id), sub_id=str(sub.id), name=sub.name)
        return sub

    async def get_subscription_by_id(
        self, sub_id: uuid.UUID, user_id: uuid.UUID
    ) -> SubscriptionModel | None:
        stmt = select(SubscriptionModel).where(
            SubscriptionModel.id == sub_id,
            SubscriptionModel.user_id == user_id,
            SubscriptionModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_subscriptions(
        self, user_id: uuid.UUID, *, status: str | None = None
    ) -> list[SubscriptionModel]:
        stmt = select(SubscriptionModel).where(
            SubscriptionModel.user_id == user_id,
            SubscriptionModel.deleted_at.is_(None),
        )
        if status:
            stmt = stmt.where(SubscriptionModel.status == status)
        stmt = stmt.order_by(SubscriptionModel.name.asc())
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update_subscription(
        self, sub_id: uuid.UUID, user_id: uuid.UUID, **kwargs: object
    ) -> SubscriptionModel | None:
        sub = await self.get_subscription_by_id(sub_id, user_id)
        if sub is None:
            return None
        for key, value in kwargs.items():
            if hasattr(sub, key):
                setattr(sub, key, value)
        await self._session.flush()
        await self._session.refresh(sub)
        return sub

    async def delete_subscription(self, sub_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        from datetime import UTC, datetime

        sub = await self.get_subscription_by_id(sub_id, user_id)
        if sub is None:
            return False
        sub.deleted_at = datetime.now(UTC)
        await self._session.flush()
        return True

    async def get_subscription_summary(self, user_id: uuid.UUID) -> dict:
        from decimal import Decimal

        stmt = select(SubscriptionModel).where(
            SubscriptionModel.user_id == user_id,
            SubscriptionModel.deleted_at.is_(None),
            SubscriptionModel.status == "active",
        )
        result = await self._session.execute(stmt)
        active = list(result.scalars().all())

        monthly_total = Decimal("0")
        annual_total = Decimal("0")
        for sub in active:
            amt = sub.amount
            if sub.billing_frequency == "monthly":
                monthly_total += amt
                annual_total += amt * 12
            elif sub.billing_frequency == "yearly":
                monthly_total += amt / 12
                annual_total += amt
            elif sub.billing_frequency == "quarterly":
                monthly_total += amt / 3
                annual_total += amt * 4
            elif sub.billing_frequency == "bimonthly":
                monthly_total += amt / 2
                annual_total += amt * 6

        return {
            "active_count": len(active),
            "monthly_total": str(round(float(monthly_total), 2)),
            "annual_total": str(round(float(annual_total), 2)),
            "subscriptions": [
                {
                    "id": str(s.id),
                    "name": s.name,
                    "amount": str(s.amount),
                    "frequency": s.billing_frequency,
                    "status": s.status,
                }
                for s in active
            ],
        }

    async def analyze_subscriptions(self, user_id: uuid.UUID) -> dict:
        """Generate subscription analysis with recommendations."""
        summary = await self.get_subscription_summary(user_id)

        recommendations: list[str] = []
        monthly = float(summary["monthly_total"])

        if monthly > 5000:
            recommendations.append(
                "Tu gasto en suscripciones es alto (>{:,.0f}/mes). Considera revisar cuales usas regularmente.".format(monthly)  # noqa: UP032
            )
        if summary["active_count"] > 5:
            recommendations.append(
                "Tienes {} suscripciones activas. Considera consolidar o cancelar las menos usadas.".format(
                    summary["active_count"]
                )
            )

        return {
            **summary,
            "recommendations": recommendations,
            "cost_per_day": str(round(monthly / 30, 2)),
        }

    # ==============================================================
    # Credit Cards CRUD
    # ==============================================================

    async def create_credit_card(self, user_id: uuid.UUID, **kwargs: object) -> CreditCardModel:
        card = CreditCardModel(user_id=user_id, **kwargs)  # type: ignore[arg-type]
        self._session.add(card)
        await self._session.flush()
        logger.info(
            "credit_card_created", user_id=str(user_id), card_id=str(card.id), name=card.name
        )
        return card

    async def get_credit_card_by_id(
        self, card_id: uuid.UUID, user_id: uuid.UUID
    ) -> CreditCardModel | None:
        stmt = select(CreditCardModel).where(
            CreditCardModel.id == card_id,
            CreditCardModel.user_id == user_id,
            CreditCardModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_credit_cards(self, user_id: uuid.UUID) -> list[CreditCardModel]:
        stmt = (
            select(CreditCardModel)
            .where(
                CreditCardModel.user_id == user_id,
                CreditCardModel.deleted_at.is_(None),
            )
            .order_by(CreditCardModel.name.asc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update_credit_card(
        self, card_id: uuid.UUID, user_id: uuid.UUID, **kwargs: object
    ) -> CreditCardModel | None:
        card = await self.get_credit_card_by_id(card_id, user_id)
        if card is None:
            return None
        for key, value in kwargs.items():
            if hasattr(card, key):
                setattr(card, key, value)
        await self._session.flush()
        await self._session.refresh(card)
        return card

    async def delete_credit_card(self, card_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        from datetime import UTC, datetime

        card = await self.get_credit_card_by_id(card_id, user_id)
        if card is None:
            return False
        card.deleted_at = datetime.now(UTC)
        await self._session.flush()
        return True

    async def get_card_utilization(self, card_id: uuid.UUID, user_id: uuid.UUID) -> dict | None:
        from decimal import Decimal

        card = await self.get_credit_card_by_id(card_id, user_id)
        if card is None:
            return None

        utilization_pct = Decimal("0")
        if card.credit_limit and card.credit_limit > 0:
            used = card.credit_limit - (card.available_credit or card.credit_limit)
            utilization_pct = (used / card.credit_limit) * 100

        return {
            "credit_limit": str(card.credit_limit or 0),
            "available_credit": str(card.available_credit or card.credit_limit or 0),
            "used_credit": str(
                (card.credit_limit or 0) - (card.available_credit or card.credit_limit or 0)
            ),
            "utilization_percentage": str(round(float(utilization_pct), 2)),
            "status": "healthy"
            if float(utilization_pct) < 30
            else "warning"
            if float(utilization_pct) < 70
            else "danger",
        }

    # ==============================================================
    # Credit Card Bills CRUD
    # ==============================================================

    async def create_card_bill(self, user_id: uuid.UUID, **kwargs: object) -> CreditCardBillModel:
        bill = CreditCardBillModel(user_id=user_id, **kwargs)  # type: ignore[arg-type]
        self._session.add(bill)
        await self._session.flush()
        logger.info("card_bill_created", user_id=str(user_id), bill_id=str(bill.id))
        return bill

    async def get_card_bill_by_id(
        self, bill_id: uuid.UUID, user_id: uuid.UUID
    ) -> CreditCardBillModel | None:
        stmt = select(CreditCardBillModel).where(
            CreditCardBillModel.id == bill_id,
            CreditCardBillModel.user_id == user_id,
            CreditCardBillModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_card_bills(
        self, user_id: uuid.UUID, credit_card_id: uuid.UUID
    ) -> list[CreditCardBillModel]:
        stmt = (
            select(CreditCardBillModel)
            .where(
                CreditCardBillModel.user_id == user_id,
                CreditCardBillModel.credit_card_id == credit_card_id,
                CreditCardBillModel.deleted_at.is_(None),
            )
            .order_by(CreditCardBillModel.statement_date.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
