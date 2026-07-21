"""Repository for credit card, bills, limits, and alerts persistence."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog
from sqlalchemy import func, select

from app.infrastructure.models.card_alert import CardAlertModel
from app.infrastructure.models.card_spending_limit import CardSpendingLimitModel
from app.infrastructure.models.credit_card import CreditCardModel
from app.infrastructure.models.credit_card_bill import CreditCardBillModel
from app.infrastructure.models.transaction import TransactionModel

if TYPE_CHECKING:
    import uuid
    from datetime import date

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class CardRepository:
    """Repository for all credit card operations."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ==============================================================
    # Credit Card CRUD
    # ==============================================================

    async def create_card(self, user_id: uuid.UUID, **kwargs: object) -> CreditCardModel:
        card = CreditCardModel(user_id=user_id, **kwargs)  # type: ignore[arg-type]
        self._session.add(card)
        await self._session.flush()
        logger.info("credit_card_created", user_id=str(user_id), card_id=str(card.id))
        return card

    async def get_card_by_id(self, card_id: uuid.UUID, user_id: uuid.UUID) -> CreditCardModel | None:
        stmt = select(CreditCardModel).where(
            CreditCardModel.id == card_id,
            CreditCardModel.user_id == user_id,
            CreditCardModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_cards(self, user_id: uuid.UUID) -> list[CreditCardModel]:
        stmt = select(CreditCardModel).where(
            CreditCardModel.user_id == user_id,
            CreditCardModel.deleted_at.is_(None),
        ).order_by(CreditCardModel.name.asc())
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update_card(self, card_id: uuid.UUID, user_id: uuid.UUID, **kwargs: object) -> CreditCardModel | None:
        card = await self.get_card_by_id(card_id, user_id)
        if card is None:
            return None
        for key, value in kwargs.items():
            if hasattr(card, key):
                setattr(card, key, value)
        await self._session.flush()
        await self._session.refresh(card)
        return card

    async def delete_card(self, card_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        from datetime import UTC, datetime as dt

        card = await self.get_card_by_id(card_id, user_id)
        if card is None:
            return False
        card.deleted_at = dt.now(UTC)
        await self._session.flush()
        return True

    # ==============================================================
    # Utilization (Transaction-based)
    # ==============================================================

    async def calculate_utilization(self, card_id: uuid.UUID, user_id: uuid.UUID) -> dict | None:
        card = await self.get_card_by_id(card_id, user_id)
        if card is None:
            return None

        from datetime import date as date_type

        today = date_type.today()
        stmt_day = card.statement_day or 1

        if today.day >= stmt_day:
            period_start = today.replace(day=stmt_day)
        else:
            if today.month == 1:
                period_start = today.replace(year=today.year - 1, month=12, day=stmt_day)
            else:
                period_start = today.replace(month=today.month - 1, day=stmt_day)

        stmt = select(func.coalesce(func.sum(TransactionModel.amount), 0)).where(
            TransactionModel.user_id == user_id,
            TransactionModel.credit_card_id == card_id,
            TransactionModel.transaction_type == "expense",
            TransactionModel.status == "completed",
            TransactionModel.effective_date >= period_start,
            TransactionModel.effective_date <= today,
            TransactionModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        used_in_cycle = float(result.scalar_one())

        credit_limit = float(card.credit_limit) if card.credit_limit else 0
        used_credit = float(card.credit_limit - card.available_credit) if card.credit_limit and card.available_credit is not None else 0
        total_used = max(used_credit, used_in_cycle)

        pct = (total_used / credit_limit * 100) if credit_limit > 0 else 0
        status = "healthy" if pct < 30 else "warning" if pct < 70 else "danger"

        return {
            "credit_limit": str(credit_limit),
            "available_credit": str(max(credit_limit - total_used, 0)),
            "used_credit": str(total_used),
            "used_in_cycle": str(used_in_cycle),
            "utilization_percentage": str(round(pct, 2)),
            "status": status,
            "period_start": period_start.isoformat(),
            "period_end": today.isoformat(),
        }

    async def get_historical_utilization(self, card_id: uuid.UUID, user_id: uuid.UUID, months: int = 6) -> list[dict]:
        from datetime import date as date_type, timedelta

        card = await self.get_card_by_id(card_id, user_id)
        if card is None:
            return []

        today = date_type.today()
        stmt_day = card.statement_day or 1
        credit_limit = float(card.credit_limit) if card.credit_limit else 0

        history: list[dict] = []
        for i in range(months):
            raw_month = today.month - i
            y = today.year
            while raw_month <= 0:
                raw_month += 12
                y -= 1

            if raw_month == 12:
                next_m_start = date_type(y + 1, 1, stmt_day)
            else:
                next_m_start = date_type(y, raw_month + 1, stmt_day)
            period_end = next_m_start - timedelta(days=1)

            try:
                period_start = date_type(y, raw_month, stmt_day)
            except ValueError:
                period_start = date_type(y, raw_month, 1)

            if period_start > today:
                continue

            stmt = select(func.coalesce(func.sum(TransactionModel.amount), 0)).where(
                TransactionModel.user_id == user_id,
                TransactionModel.credit_card_id == card_id,
                TransactionModel.transaction_type == "expense",
                TransactionModel.status == "completed",
                TransactionModel.effective_date >= period_start,
                TransactionModel.effective_date <= period_end,
                TransactionModel.deleted_at.is_(None),
            )
            result = await self._session.execute(stmt)
            spent = float(result.scalar_one())
            pct = (spent / credit_limit * 100) if credit_limit > 0 else 0

            history.append({
                "month": period_start.isoformat(),
                "spent": str(round(spent, 2)),
                "credit_limit": str(credit_limit),
                "utilization_pct": str(round(pct, 2)),
                "status": "healthy" if pct < 30 else "warning" if pct < 70 else "danger",
            })

        history.reverse()
        return history

    async def get_spending_by_category(
        self, card_id: uuid.UUID, user_id: uuid.UUID,
        period_start: date | None = None, period_end: date | None = None,
    ) -> list[dict]:
        from datetime import date as date_type

        if not period_start:
            today = date_type.today()
            period_start = today.replace(day=1)
        if not period_end:
            period_end = date_type.today()

        stmt = (
            select(
                TransactionModel.category_id,
                func.coalesce(func.sum(TransactionModel.amount), 0).label("total"),
                func.count().label("transaction_count"),
            )
            .where(
                TransactionModel.user_id == user_id,
                TransactionModel.credit_card_id == card_id,
                TransactionModel.transaction_type == "expense",
                TransactionModel.status == "completed",
                TransactionModel.effective_date >= period_start,
                TransactionModel.effective_date <= period_end,
                TransactionModel.deleted_at.is_(None),
            )
            .group_by(TransactionModel.category_id)
            .order_by(func.sum(TransactionModel.amount).desc())
        )
        result = await self._session.execute(stmt)
        return [
            {
                "category_id": str(row[0]) if row[0] else None,
                "total": str(round(float(row[1]), 2)),
                "transaction_count": row[2],
            }
            for row in result.all()
        ]

    # ==============================================================
    # Credit Card Bills CRUD
    # ==============================================================

    async def create_bill(self, user_id: uuid.UUID, **kwargs: object) -> CreditCardBillModel:
        bill = CreditCardBillModel(user_id=user_id, **kwargs)  # type: ignore[arg-type]
        self._session.add(bill)
        await self._session.flush()
        logger.info("card_bill_created", user_id=str(user_id), bill_id=str(bill.id))
        return bill

    async def get_bill_by_id(self, bill_id: uuid.UUID, user_id: uuid.UUID) -> CreditCardBillModel | None:
        stmt = select(CreditCardBillModel).where(
            CreditCardBillModel.id == bill_id,
            CreditCardBillModel.user_id == user_id,
            CreditCardBillModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_bills(self, user_id: uuid.UUID, credit_card_id: uuid.UUID) -> list[CreditCardBillModel]:
        stmt = select(CreditCardBillModel).where(
            CreditCardBillModel.user_id == user_id,
            CreditCardBillModel.credit_card_id == credit_card_id,
            CreditCardBillModel.deleted_at.is_(None),
        ).order_by(CreditCardBillModel.statement_date.desc())
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update_bill(self, bill_id: uuid.UUID, user_id: uuid.UUID, **kwargs: object) -> CreditCardBillModel | None:
        bill = await self.get_bill_by_id(bill_id, user_id)
        if bill is None:
            return None
        for key, value in kwargs.items():
            if hasattr(bill, key):
                setattr(bill, key, value)
        await self._session.flush()
        await self._session.refresh(bill)
        return bill

    async def delete_bill(self, bill_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        from datetime import UTC, datetime as dt

        bill = await self.get_bill_by_id(bill_id, user_id)
        if bill is None:
            return False
        bill.deleted_at = dt.now(UTC)
        await self._session.flush()
        return True

    async def pay_bill(
        self, bill_id: uuid.UUID, user_id: uuid.UUID,
        amount: float, payment_method: str = "manual",
    ) -> CreditCardBillModel | None:
        from datetime import UTC, datetime as dt

        bill = await self.get_bill_by_id(bill_id, user_id)
        if bill is None:
            return None

        new_amount_paid = float(bill.amount_paid) + amount
        total = float(bill.total_amount)

        if new_amount_paid >= total:
            bill.payment_status = "paid"
            bill.amount_paid = total
            bill.paid_at = dt.now(UTC)
        elif new_amount_paid > 0:
            bill.payment_status = "partial"
            bill.amount_paid = new_amount_paid
        else:
            bill.payment_status = "pending"

        await self._session.flush()
        await self._session.refresh(bill)

        logger.info(
            "bill_payment",
            user_id=str(user_id),
            bill_id=str(bill.id),
            amount=amount,
            new_status=bill.payment_status,
            payment_method=payment_method,
        )
        return bill

    async def generate_statement(self, credit_card_id: uuid.UUID, user_id: uuid.UUID) -> CreditCardBillModel | None:
        from datetime import date as date_type, timedelta

        card = await self.get_card_by_id(credit_card_id, user_id)
        if card is None:
            return None

        today = date_type.today()
        stmt_day = card.statement_day or 1
        due_day = card.payment_due_day or min(stmt_day + 20, 28)

        if today.day >= stmt_day:
            period_start = today.replace(day=stmt_day)
            if today.month == 12:
                period_end = today.replace(year=today.year + 1, month=1, day=stmt_day) - timedelta(days=1)
            else:
                period_end = today.replace(month=today.month + 1, day=stmt_day) - timedelta(days=1)
        else:
            if today.month == 1:
                period_start = today.replace(year=today.year - 1, month=12, day=stmt_day)
            else:
                period_start = today.replace(month=today.month - 1, day=stmt_day)
            period_end = today.replace(day=stmt_day) - timedelta(days=1)

        stmt = select(func.coalesce(func.sum(TransactionModel.amount), 0)).where(
            TransactionModel.user_id == user_id,
            TransactionModel.credit_card_id == credit_card_id,
            TransactionModel.transaction_type == "expense",
            TransactionModel.status == "completed",
            TransactionModel.effective_date >= period_start,
            TransactionModel.effective_date <= period_end,
            TransactionModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        total_amount = float(result.scalar_one())

        count_stmt = select(func.count()).select_from(TransactionModel).where(
            TransactionModel.user_id == user_id,
            TransactionModel.credit_card_id == credit_card_id,
            TransactionModel.transaction_type == "expense",
            TransactionModel.status == "completed",
            TransactionModel.effective_date >= period_start,
            TransactionModel.effective_date <= period_end,
            TransactionModel.deleted_at.is_(None),
        )
        count_result = await self._session.execute(count_stmt)
        tx_count = count_result.scalar_one()

        interest = total_amount * (float(card.interest_rate) / 100 / 12) if card.interest_rate else 0
        minimum = max(total_amount * 0.05, 500) if total_amount > 0 else 0

        due_date = period_end.replace(day=due_day)
        if due_date <= period_end:
            if due_date.month == 12:
                due_date = due_date.replace(year=due_date.year + 1, month=1, day=due_day)
            else:
                due_date = due_date.replace(month=due_date.month + 1, day=due_day)

        bill = await self.create_bill(
            user_id,
            credit_card_id=credit_card_id,
            statement_date=period_start,
            due_date=due_date,
            total_amount=total_amount,
            minimum_payment=round(minimum, 2),
            interest_charged=round(interest, 2),
            payment_status="pending",
            amount_paid=0,
            transaction_count=tx_count,
        )

        logger.info(
            "statement_generated",
            user_id=str(user_id),
            card_id=str(credit_card_id),
            total_amount=total_amount,
            tx_count=tx_count,
        )
        return bill

    # ==============================================================
    # Spending Limits CRUD
    # ==============================================================

    async def create_spending_limit(self, user_id: uuid.UUID, **kwargs: object) -> CardSpendingLimitModel:
        limit = CardSpendingLimitModel(user_id=user_id, **kwargs)  # type: ignore[arg-type]
        self._session.add(limit)
        await self._session.flush()
        logger.info("card_limit_created", user_id=str(user_id), limit_id=str(limit.id))
        return limit

    async def get_limit_by_id(self, limit_id: uuid.UUID, user_id: uuid.UUID) -> CardSpendingLimitModel | None:
        stmt = select(CardSpendingLimitModel).where(
            CardSpendingLimitModel.id == limit_id,
            CardSpendingLimitModel.user_id == user_id,
            CardSpendingLimitModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_limits(self, user_id: uuid.UUID, credit_card_id: uuid.UUID) -> list[CardSpendingLimitModel]:
        stmt = select(CardSpendingLimitModel).where(
            CardSpendingLimitModel.user_id == user_id,
            CardSpendingLimitModel.credit_card_id == credit_card_id,
            CardSpendingLimitModel.deleted_at.is_(None),
        ).order_by(CardSpendingLimitModel.created_at.desc())
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update_limit(self, limit_id: uuid.UUID, user_id: uuid.UUID, **kwargs: object) -> CardSpendingLimitModel | None:
        limit = await self.get_limit_by_id(limit_id, user_id)
        if limit is None:
            return None
        for key, value in kwargs.items():
            if hasattr(limit, key):
                setattr(limit, key, value)
        await self._session.flush()
        await self._session.refresh(limit)
        return limit

    async def delete_limit(self, limit_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        from datetime import UTC, datetime as dt

        limit = await self.get_limit_by_id(limit_id, user_id)
        if limit is None:
            return False
        limit.deleted_at = dt.now(UTC)
        await self._session.flush()
        return True

    async def recalculate_limit_spent(self, limit_id: uuid.UUID, user_id: uuid.UUID) -> CardSpendingLimitModel | None:
        from datetime import date as date_type, timedelta

        limit = await self.get_limit_by_id(limit_id, user_id)
        if limit is None:
            return None

        today = date_type.today()

        if limit.limit_type == "daily":
            period_start = today
            period_end = today
        elif limit.limit_type == "weekly":
            period_start = today - timedelta(days=today.weekday())
            period_end = today
        else:
            period_start = today.replace(day=1)
            period_end = today

        stmt = select(func.coalesce(func.sum(TransactionModel.amount), 0)).where(
            TransactionModel.user_id == user_id,
            TransactionModel.credit_card_id == limit.credit_card_id,
            TransactionModel.transaction_type == "expense",
            TransactionModel.status == "completed",
            TransactionModel.effective_date >= period_start,
            TransactionModel.effective_date <= period_end,
            TransactionModel.deleted_at.is_(None),
        )
        if limit.category_id:
            stmt = stmt.where(TransactionModel.category_id == limit.category_id)

        result = await self._session.execute(stmt)
        spent = float(result.scalar_one())

        from datetime import datetime as dt_type

        limit.spent_amount = spent
        limit.period_start = dt_type.combine(period_start, dt_type.min.time()).replace(tzinfo=None)
        limit.period_end = dt_type.combine(period_end, dt_type.max.time()).replace(tzinfo=None)
        await self._session.flush()
        await self._session.refresh(limit)
        return limit

    # ==============================================================
    # Card Alerts CRUD
    # ==============================================================

    async def create_alert(self, user_id: uuid.UUID, **kwargs: object) -> CardAlertModel:
        alert = CardAlertModel(user_id=user_id, **kwargs)  # type: ignore[arg-type]
        self._session.add(alert)
        await self._session.flush()
        logger.info("card_alert_created", user_id=str(user_id), alert_type=alert.alert_type)
        return alert

    async def list_alerts(
        self,
        user_id: uuid.UUID,
        *,
        credit_card_id: uuid.UUID | None = None,
        is_read: bool | None = None,
        is_dismissed: bool | None = None,
        alert_type: str | None = None,
        severity: str | None = None,
    ) -> list[CardAlertModel]:
        stmt = select(CardAlertModel).where(CardAlertModel.user_id == user_id)
        if credit_card_id:
            stmt = stmt.where(CardAlertModel.credit_card_id == credit_card_id)
        if is_read is not None:
            stmt = stmt.where(CardAlertModel.is_read == is_read)
        if is_dismissed is not None:
            stmt = stmt.where(CardAlertModel.is_dismissed == is_dismissed)
        if alert_type:
            stmt = stmt.where(CardAlertModel.alert_type == alert_type)
        if severity:
            stmt = stmt.where(CardAlertModel.severity == severity)
        stmt = stmt.order_by(CardAlertModel.triggered_at.desc())
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_alert_by_id(self, alert_id: uuid.UUID, user_id: uuid.UUID) -> CardAlertModel | None:
        stmt = select(CardAlertModel).where(
            CardAlertModel.id == alert_id,
            CardAlertModel.user_id == user_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def mark_alert_read(self, alert_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        from datetime import UTC, datetime as dt

        alert = await self.get_alert_by_id(alert_id, user_id)
        if alert is None:
            return False
        alert.is_read = True
        alert.read_at = dt.now(UTC)
        await self._session.flush()
        return True

    async def mark_all_alerts_read(self, user_id: uuid.UUID) -> int:
        from datetime import UTC, datetime as dt

        stmt = select(CardAlertModel).where(
            CardAlertModel.user_id == user_id,
            CardAlertModel.is_read.is_(False),
        )
        result = await self._session.execute(stmt)
        alerts = list(result.scalars().all())
        now = dt.now(UTC)
        for alert in alerts:
            alert.is_read = True
            alert.read_at = now
        await self._session.flush()
        return len(alerts)

    async def dismiss_alert(self, alert_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        from datetime import UTC, datetime as dt

        alert = await self.get_alert_by_id(alert_id, user_id)
        if alert is None:
            return False
        alert.is_dismissed = True
        alert.dismissed_at = dt.now(UTC)
        await self._session.flush()
        return True

    async def get_unread_alert_count(self, user_id: uuid.UUID) -> int:
        stmt = select(func.count()).select_from(CardAlertModel).where(
            CardAlertModel.user_id == user_id,
            CardAlertModel.is_read.is_(False),
            CardAlertModel.is_dismissed.is_(False),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def check_and_create_alerts(self, user_id: uuid.UUID) -> list[CardAlertModel]:
        cards = await self.list_cards(user_id)
        new_alerts: list[CardAlertModel] = []

        for card in cards:
            if not card.credit_limit:
                continue

            util = await self.calculate_utilization(card.id, user_id)
            if util:
                pct = float(util["utilization_percentage"])
                existing = await self.list_alerts(user_id, credit_card_id=card.id)
                existing_types = {a.alert_type for a in existing}

                if pct >= 90 and "high_utilization" not in existing_types:
                    alert = await self.create_alert(
                        user_id,
                        credit_card_id=card.id,
                        alert_type="high_utilization",
                        severity="critical",
                        title=f"Utilizacion alta: {card.name}",
                        message=f"Tu tarjeta '{card.name}' esta al {pct:.1f}% de utilizacion. Limite: ${float(card.credit_limit):,.2f}.",
                        threshold_percentage=90,
                        current_amount=util["used_credit"],
                        limit_amount=str(card.credit_limit),
                    )
                    new_alerts.append(alert)
                elif pct >= 70 and "limit_approaching" not in existing_types:
                    alert = await self.create_alert(
                        user_id,
                        credit_card_id=card.id,
                        alert_type="limit_approaching",
                        severity="warning",
                        title=f"Limite cercano: {card.name}",
                        message=f"Tu tarjeta '{card.name}' esta al {pct:.1f}% de utilizacion. Credito disponible: ${util['available_credit']}.",
                        threshold_percentage=70,
                        current_amount=util["used_credit"],
                        limit_amount=str(card.credit_limit),
                    )
                    new_alerts.append(alert)

            from datetime import date as date_type, timedelta

            today = date_type.today()
            upcoming = today + timedelta(days=7)
            bills = await self.list_bills(user_id, card.id)
            for bill in bills:
                if bill.payment_status in ("pending", "partial") and bill.due_date <= upcoming:
                    existing = await self.list_alerts(user_id, credit_card_id=card.id)
                    existing_bill_ids = {str(a.credit_card_bill_id) for a in existing if a.credit_card_bill_id}

                    if str(bill.id) not in existing_bill_ids:
                        days_left = (bill.due_date - today).days
                        severity = "critical" if days_left <= 2 else "warning"
                        alert = await self.create_alert(
                            user_id,
                            credit_card_id=card.id,
                            credit_card_bill_id=bill.id,
                            alert_type="due_date_approaching",
                            severity=severity,
                            title=f"Pago vence en {days_left} dias: {card.name}",
                            message=(
                                f"La factura de '{card.name}' vence el {bill.due_date.isoformat()}. "
                                f"Saldo: ${float(bill.total_amount):,.2f}. "
                                f"Pago minimo: ${float(bill.minimum_payment or 0):,.2f}."
                            ),
                            current_amount=bill.total_amount,
                            limit_amount=str(card.credit_limit),
                        )
                        new_alerts.append(alert)

                if bill.payment_status in ("pending", "partial") and bill.due_date < today:
                    existing = await self.list_alerts(user_id, credit_card_id=card.id)
                    overdue_types = {a.alert_type for a in existing if a.credit_card_bill_id == bill.id}
                    if "payment_overdue" not in overdue_types:
                        days_overdue = (today - bill.due_date).days
                        alert = await self.create_alert(
                            user_id,
                            credit_card_id=card.id,
                            credit_card_bill_id=bill.id,
                            alert_type="payment_overdue",
                            severity="critical",
                            title=f"Pago vencido ({days_overdue} dias): {card.name}",
                            message=(
                                f"La factura de '{card.name}' vencio hace {days_overdue} dias. "
                                f"Saldo: ${float(bill.total_amount):,.2f}. "
                                f"Realiza tu pago lo antes posible."
                            ),
                            current_amount=bill.total_amount,
                            limit_amount=str(card.credit_limit),
                        )
                        new_alerts.append(alert)

        return new_alerts

    # ==============================================================
    # Card Portfolio Summary
    # ==============================================================

    async def get_cards_summary(self, user_id: uuid.UUID) -> dict:
        cards = await self.list_cards(user_id)
        total_limit = sum(float(c.credit_limit) for c in cards if c.credit_limit)
        total_used = sum(
            float(c.credit_limit - c.available_credit)
            for c in cards
            if c.credit_limit and c.available_credit is not None
        )
        total_available = total_limit - total_used
        avg_utilization = (total_used / total_limit * 100) if total_limit > 0 else 0

        unpaid_bills = 0
        total_minimum = 0.0
        for card in cards:
            bills = await self.list_bills(user_id, card.id)
            for b in bills:
                if b.payment_status in ("pending", "partial"):
                    unpaid_bills += 1
                    total_minimum += float(b.minimum_payment or 0)

        return {
            "total_cards": len(cards),
            "total_credit_limit": str(round(total_limit, 2)),
            "total_used_credit": str(round(total_used, 2)),
            "total_available_credit": str(round(total_available, 2)),
            "average_utilization_pct": str(round(avg_utilization, 2)),
            "unpaid_bills": unpaid_bills,
            "total_minimum_payment": str(round(total_minimum, 2)),
            "cards": [
                {
                    "id": str(c.id),
                    "name": c.name,
                    "last_four_digits": c.last_four_digits,
                    "card_network": c.card_network,
                    "credit_limit": str(c.credit_limit) if c.credit_limit else None,
                    "is_active": c.is_active,
                    "color": c.color,
                }
                for c in cards
            ],
        }
