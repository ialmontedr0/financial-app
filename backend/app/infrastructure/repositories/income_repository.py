"""Repository for income module persistence."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog
from sqlalchemy import and_, func, select

from app.infrastructure.models.income import IncomeModel
from app.infrastructure.models.income_schedule import IncomeScheduleModel
from app.infrastructure.models.income_source import IncomeSourceModel
from app.infrastructure.models.transaction import TransactionModel

if TYPE_CHECKING:
    import uuid
    from datetime import date
    from decimal import Decimal

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class IncomeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ==============================================================
    # Income CRUD
    # ==============================================================

    async def create_income(self, user_id: uuid.UUID, *, transaction_id: uuid.UUID,
        income_type: str = "salary", income_status: str = "received",
        stability: str = "fixed", income_source_id: uuid.UUID | None = None,
        employer_name: str | None = None, employer_tax_id: str | None = None,
        gross_amount: Decimal | None = None, tax_withheld: Decimal | None = None,
        net_amount: Decimal | None = None, frequency: str | None = None,
        effective_date: date | None = None, notes: str | None = None,
    ) -> IncomeModel:
        from datetime import date as date_type
        income = IncomeModel(
            user_id=user_id, transaction_id=transaction_id,
            income_type=income_type, income_status=income_status,
            stability=stability, income_source_id=income_source_id,
            employer_name=employer_name, employer_tax_id=employer_tax_id,
            gross_amount=gross_amount, tax_withheld=tax_withheld, net_amount=net_amount,
            frequency=frequency, effective_date=effective_date or date_type.today(),
            notes=notes,
        )
        self._session.add(income)
        await self._session.flush()
        logger.info("income_created", user_id=str(user_id), income_id=str(income.id))
        return income

    async def get_income_by_id(self, income_id: uuid.UUID, user_id: uuid.UUID) -> IncomeModel | None:
        stmt = select(IncomeModel).where(
            IncomeModel.id == income_id, IncomeModel.user_id == user_id, IncomeModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_income_by_transaction_id(self, transaction_id: uuid.UUID) -> IncomeModel | None:
        stmt = select(IncomeModel).where(
            IncomeModel.transaction_id == transaction_id, IncomeModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_income(self, income_id: uuid.UUID, user_id: uuid.UUID, **kwargs: object) -> IncomeModel | None:
        income = await self.get_income_by_id(income_id, user_id)
        if income is None:
            return None
        for key, value in kwargs.items():
            if hasattr(income, key):
                setattr(income, key, value)
        await self._session.flush()
        await self._session.refresh(income)
        return income

    async def delete_income(self, income_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        from datetime import UTC, datetime
        income = await self.get_income_by_id(income_id, user_id)
        if income is None:
            return False
        income.deleted_at = datetime.now(UTC)
        await self._session.flush()
        return True

    async def list_incomes(self, user_id: uuid.UUID, *,
        income_type: str | None = None, income_status: str | None = None,
        stability: str | None = None, income_source_id: uuid.UUID | None = None,
        category_id: uuid.UUID | None = None, account_id: uuid.UUID | None = None,
        min_amount: float | None = None, max_amount: float | None = None,
        date_from: date | None = None, date_to: date | None = None,
        search: str | None = None, sort_by: str = "effective_date",
        sort_order: str = "desc", page: int = 1, page_size: int = 20,
    ) -> tuple[list[IncomeModel], int]:
        filters = [IncomeModel.user_id == user_id, IncomeModel.deleted_at.is_(None)]
        if income_type:
            filters.append(IncomeModel.income_type == income_type)
        if income_status:
            filters.append(IncomeModel.income_status == income_status)
        if stability:
            filters.append(IncomeModel.stability == stability)
        if income_source_id:
            filters.append(IncomeModel.income_source_id == income_source_id)
        if date_from:
            filters.append(IncomeModel.effective_date >= date_from)
        if date_to:
            filters.append(IncomeModel.effective_date <= date_to)

        count_stmt = select(func.count(IncomeModel.id)).where(and_(*filters))
        count_result = await self._session.execute(count_stmt)
        total = count_result.scalar() or 0

        stmt = select(IncomeModel).join(TransactionModel, IncomeModel.transaction_id == TransactionModel.id).where(and_(*filters))
        if min_amount is not None:
            stmt = stmt.where(TransactionModel.amount >= min_amount)
        if max_amount is not None:
            stmt = stmt.where(TransactionModel.amount <= max_amount)
        if search:
            stmt = stmt.where(TransactionModel.description.ilike(f"%{search}%"))

        sort_col = getattr(IncomeModel, sort_by, IncomeModel.effective_date)
        stmt = stmt.order_by(sort_col.desc() if sort_order == "desc" else sort_col.asc())
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        result = await self._session.execute(stmt)
        return list(result.scalars().all()), total

    # ==============================================================
    # Income Analytics
    # ==============================================================

    async def get_income_summary(self, user_id: uuid.UUID, date_from: date, date_to: date) -> dict:
        from decimal import Decimal
        base_filter = and_(IncomeModel.user_id == user_id, IncomeModel.deleted_at.is_(None),
            IncomeModel.effective_date >= date_from, IncomeModel.effective_date <= date_to)

        stmt = select(func.count(IncomeModel.id).label("count"), func.sum(TransactionModel.amount).label("total")
        ).join(TransactionModel, IncomeModel.transaction_id == TransactionModel.id).where(base_filter)
        row = (await self._session.execute(stmt)).one()
        total_amount = Decimal(str(row.total or 0))

        type_stmt = select(IncomeModel.income_type, func.count(IncomeModel.id).label("count"),
            func.sum(TransactionModel.amount).label("total")
        ).join(TransactionModel, IncomeModel.transaction_id == TransactionModel.id
        ).where(base_filter).group_by(IncomeModel.income_type).order_by(func.sum(TransactionModel.amount).desc())
        by_type = [{"type": r.income_type, "count": r.count, "total": str(r.total or 0),
            "percentage": str(round(float(r.total or 0) / float(total_amount) * 100, 2)) if total_amount > 0 else "0"
        } for r in (await self._session.execute(type_stmt)).all()]

        stab_stmt = select(IncomeModel.stability, func.count(IncomeModel.id).label("count"),
            func.sum(TransactionModel.amount).label("total")
        ).join(TransactionModel, IncomeModel.transaction_id == TransactionModel.id
        ).where(base_filter).group_by(IncomeModel.stability)
        by_stability = [{"stability": r.stability, "count": r.count, "total": str(r.total or 0)}
            for r in (await self._session.execute(stab_stmt)).all()]

        source_stmt = select(IncomeSourceModel.name, func.count(IncomeModel.id).label("count"),
            func.sum(TransactionModel.amount).label("total")
        ).join(TransactionModel, IncomeModel.transaction_id == TransactionModel.id
        ).join(IncomeSourceModel, IncomeModel.income_source_id == IncomeSourceModel.id, isouter=True
        ).where(base_filter).group_by(IncomeSourceModel.name)
        by_source = [{"source": r.name or "Sin fuente", "count": r.count, "total": str(r.total or 0)}
            for r in (await self._session.execute(source_stmt)).all()]

        months = max(1, (date_to - date_from).days // 30)
        avg_monthly = total_amount / months

        tax_stmt = select(func.sum(IncomeModel.gross_amount).label("gross"),
            func.sum(IncomeModel.tax_withheld).label("withheld")).where(base_filter)
        tax_row = (await self._session.execute(tax_stmt)).one()

        return {
            "period_start": date_from.isoformat(), "period_end": date_to.isoformat(),
            "total_income": str(total_amount), "total_count": row.count or 0,
            "average_monthly_income": str(round(float(avg_monthly), 2)),
            "gross_income": str(tax_row.gross or 0), "total_tax_withheld": str(tax_row.withheld or 0),
            "net_income": str(float(total_amount) - float(tax_row.withheld or 0)),
            "by_type": by_type, "by_stability": by_stability, "by_source": by_source,
        }

    async def get_income_trends(self, user_id: uuid.UUID, months: int = 12) -> dict:
        from decimal import Decimal
        from datetime import date as date_type, timedelta
        today = date_type.today()
        start = today - timedelta(days=months * 30)
        stmt = select(func.extract("year", IncomeModel.effective_date).label("year"),
            func.extract("month", IncomeModel.effective_date).label("month"),
            func.sum(TransactionModel.amount).label("total"), func.count(IncomeModel.id).label("count"),
        ).join(TransactionModel, IncomeModel.transaction_id == TransactionModel.id
        ).where(IncomeModel.user_id == user_id, IncomeModel.deleted_at.is_(None), IncomeModel.effective_date >= start
        ).group_by(func.extract("year", IncomeModel.effective_date), func.extract("month", IncomeModel.effective_date)
        ).order_by(func.extract("year", IncomeModel.effective_date).asc(), func.extract("month", IncomeModel.effective_date).asc())
        monthly_data = [{"year": int(r.year), "month": int(r.month), "total": str(r.total or 0), "count": r.count}
            for r in (await self._session.execute(stmt)).all()]
        trend = "insufficient_data"
        if len(monthly_data) >= 2:
            recent, prev = Decimal(monthly_data[-1]["total"]), Decimal(monthly_data[-2]["total"])
            trend = "increasing" if recent > prev else "decreasing" if recent < prev else "stable"
        totals = [Decimal(m["total"]) for m in monthly_data]
        avg = sum(totals) / len(totals) if totals else Decimal("0")
        return {"monthly_data": monthly_data, "trend": trend, "average_monthly": str(round(float(avg), 2)), "period_months": months}

    async def get_income_by_source(self, user_id: uuid.UUID, date_from: date, date_to: date) -> list[dict]:
        stmt = select(IncomeSourceModel.id, IncomeSourceModel.name, IncomeSourceModel.income_type,
            func.count(IncomeModel.id).label("count"), func.sum(TransactionModel.amount).label("total"),
        ).join(TransactionModel, IncomeModel.transaction_id == TransactionModel.id
        ).join(IncomeSourceModel, IncomeModel.income_source_id == IncomeSourceModel.id, isouter=True
        ).where(IncomeModel.user_id == user_id, IncomeModel.deleted_at.is_(None),
            IncomeModel.effective_date >= date_from, IncomeModel.effective_date <= date_to
        ).group_by(IncomeSourceModel.id, IncomeSourceModel.name, IncomeSourceModel.income_type
        ).order_by(func.sum(TransactionModel.amount).desc())
        return [{"source_id": str(r.id), "source_name": r.name or "Sin fuente",
            "income_type": r.income_type, "count": r.count, "total": str(r.total or 0)}
            for r in (await self._session.execute(stmt)).all()]

    async def get_monthly_breakdown(self, user_id: uuid.UUID, year: int, month: int) -> dict:
        from decimal import Decimal
        stmt = select(TransactionModel.amount, TransactionModel.description, TransactionModel.effective_date,
            IncomeModel.income_type, IncomeModel.stability, IncomeSourceModel.name.label("source_name"),
        ).join(TransactionModel, IncomeModel.transaction_id == TransactionModel.id
        ).join(IncomeSourceModel, IncomeModel.income_source_id == IncomeSourceModel.id, isouter=True
        ).where(IncomeModel.user_id == user_id, IncomeModel.deleted_at.is_(None),
            func.extract("year", IncomeModel.effective_date) == year,
            func.extract("month", IncomeModel.effective_date) == month,
        ).order_by(TransactionModel.effective_date.desc())
        items, total = [], Decimal("0")
        for r in (await self._session.execute(stmt)).all():
            items.append({"amount": str(r.amount), "description": r.description,
                "date": r.effective_date.isoformat() if r.effective_date else None,
                "income_type": r.income_type, "stability": r.stability, "source": r.source_name})
            total += r.amount
        return {"year": year, "month": month, "total": str(total), "count": len(items), "incomes": items}

    async def detect_recurring_incomes(self, user_id: uuid.UUID) -> list[dict]:
        from collections import defaultdict
        from datetime import date as date_type, timedelta
        today = date_type.today()
        cutoff = today - timedelta(days=180)
        stmt = select(TransactionModel).where(TransactionModel.user_id == user_id,
            TransactionModel.deleted_at.is_(None), TransactionModel.transaction_type == "income",
            TransactionModel.effective_date >= cutoff).order_by(TransactionModel.amount.asc())
        txs = list((await self._session.execute(stmt)).scalars().all())
        groups: dict[str, list] = defaultdict(list)
        for tx in txs:
            key = f"{(tx.description or '').lower().strip()[:20]}_{tx.amount}"
            groups[key].append(tx)
        candidates = []
        for group in groups.values():
            if len(group) >= 2:
                dates = sorted([tx.effective_date for tx in group])
                gaps = [(dates[i+1] - dates[i]).days for i in range(len(dates)-1)]
                avg_gap = sum(gaps) / len(gaps) if gaps else 0
                candidates.append({"description": group[0].description, "amount": str(group[0].amount),
                    "occurrences": len(group), "avg_frequency_days": round(avg_gap, 1),
                    "is_monthly_like": 25 <= avg_gap <= 35,
                    "first_date": dates[0].isoformat(), "last_date": dates[-1].isoformat(),
                    "sample_transaction_id": str(group[0].id)})
        candidates.sort(key=lambda x: x["occurrences"], reverse=True)
        return candidates

    async def detect_irregular_income(self, user_id: uuid.UUID, months: int = 6) -> list[dict]:
        from datetime import date as date_type, timedelta
        cutoff = date_type.today() - timedelta(days=months * 30)
        sources_stmt = select(IncomeSourceModel).where(IncomeSourceModel.user_id == user_id,
            IncomeSourceModel.is_active.is_(True), IncomeSourceModel.deleted_at.is_(None))
        sources = list((await self._session.execute(sources_stmt)).scalars().all())
        irregularities = []
        for source in sources:
            stmt = select(TransactionModel.amount, TransactionModel.effective_date
            ).join(IncomeModel, IncomeModel.transaction_id == TransactionModel.id
            ).where(IncomeModel.user_id == user_id, IncomeModel.income_source_id == source.id,
                IncomeModel.deleted_at.is_(None), TransactionModel.effective_date >= cutoff
            ).order_by(TransactionModel.effective_date.desc())
            txs = (await self._session.execute(stmt)).all()
            if not txs:
                irregularities.append({"source_id": str(source.id), "source_name": source.name,
                    "type": "missing_income", "message": f"No se detectaron ingresos de '{source.name}'"})
            elif source.frequency == "monthly" and len(txs) < months - 1:
                irregularities.append({"source_id": str(source.id), "source_name": source.name,
                    "type": "incomplete", "message": f"Esperados ~{months} pagos, recibidos {len(txs)}"})
        return irregularities

    async def get_income_forecast(self, user_id: uuid.UUID) -> dict:
        from decimal import Decimal
        from datetime import date as date_type, timedelta
        today = date_type.today()
        async def _avg(start):
            stmt = select(func.sum(TransactionModel.amount)).join(IncomeModel, IncomeModel.transaction_id == TransactionModel.id
            ).where(IncomeModel.user_id == user_id, IncomeModel.deleted_at.is_(None), IncomeModel.effective_date >= start)
            total = (await self._session.execute(stmt)).scalar() or 0
            months = max(1, (today - start).days // 30)
            return Decimal(str(total)) / months
        avg_3m = await _avg(today - timedelta(days=90))
        avg_6m = await _avg(today - timedelta(days=180))
        avg_12m = await _avg(today - timedelta(days=365))
        trend = "increasing" if avg_3m > avg_6m > avg_12m else "decreasing" if avg_3m < avg_6m < avg_12m else "stable"
        return {"average_monthly_3m": str(round(float(avg_3m), 2)), "average_monthly_6m": str(round(float(avg_6m), 2)),
            "average_monthly_12m": str(round(float(avg_12m), 2)), "trend": trend,
            "projected_next_6m": str(round(float(avg_3m * 6), 2)), "projected_monthly": str(round(float(avg_3m), 2))}

    # ==============================================================
    # Income Source CRUD
    # ==============================================================

    async def create_source(self, user_id: uuid.UUID, **kwargs: object) -> IncomeSourceModel:
        source = IncomeSourceModel(user_id=user_id, **kwargs)  # type: ignore[arg-type]
        self._session.add(source)
        await self._session.flush()
        return source

    async def get_source_by_id(self, source_id: uuid.UUID, user_id: uuid.UUID) -> IncomeSourceModel | None:
        stmt = select(IncomeSourceModel).where(IncomeSourceModel.id == source_id,
            IncomeSourceModel.user_id == user_id, IncomeSourceModel.deleted_at.is_(None))
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def list_sources(self, user_id: uuid.UUID, *, is_active: bool | None = None,
        income_type: str | None = None) -> list[IncomeSourceModel]:
        stmt = select(IncomeSourceModel).where(IncomeSourceModel.user_id == user_id, IncomeSourceModel.deleted_at.is_(None))
        if is_active is not None:
            stmt = stmt.where(IncomeSourceModel.is_active == is_active)
        if income_type:
            stmt = stmt.where(IncomeSourceModel.income_type == income_type)
        return list((await self._session.execute(stmt.order_by(IncomeSourceModel.name.asc()))).scalars().all())

    async def update_source(self, source_id: uuid.UUID, user_id: uuid.UUID, **kwargs: object) -> IncomeSourceModel | None:
        source = await self.get_source_by_id(source_id, user_id)
        if source is None:
            return None
        for k, v in kwargs.items():
            if hasattr(source, k):
                setattr(source, k, v)
        await self._session.flush()
        await self._session.refresh(source)
        return source

    async def delete_source(self, source_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        from datetime import UTC, datetime
        source = await self.get_source_by_id(source_id, user_id)
        if source is None:
            return False
        source.deleted_at = datetime.now(UTC)
        await self._session.flush()
        return True

    async def increment_source_stats(self, source_id: uuid.UUID, amount: Decimal) -> None:
        from datetime import UTC, datetime
        source = await self._session.get(IncomeSourceModel, source_id)
        if source:
            source.total_received = (source.total_received or 0) + amount
            source.income_count += 1
            source.last_received_at = datetime.now(UTC)
            await self._session.flush()

    # ==============================================================
    # Income Schedule CRUD
    # ==============================================================

    async def create_schedule(self, user_id: uuid.UUID, **kwargs: object) -> IncomeScheduleModel:
        schedule = IncomeScheduleModel(user_id=user_id, **kwargs)  # type: ignore[arg-type]
        self._session.add(schedule)
        await self._session.flush()
        return schedule

    async def get_schedule_by_id(self, schedule_id: uuid.UUID, user_id: uuid.UUID) -> IncomeScheduleModel | None:
        stmt = select(IncomeScheduleModel).where(IncomeScheduleModel.id == schedule_id,
            IncomeScheduleModel.user_id == user_id, IncomeScheduleModel.deleted_at.is_(None))
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def list_schedules(self, user_id: uuid.UUID, *, status: str | None = None,
        date_from: date | None = None, date_to: date | None = None) -> list[IncomeScheduleModel]:
        stmt = select(IncomeScheduleModel).where(IncomeScheduleModel.user_id == user_id, IncomeScheduleModel.deleted_at.is_(None))
        if status:
            stmt = stmt.where(IncomeScheduleModel.status == status)
        if date_from:
            stmt = stmt.where(IncomeScheduleModel.expected_date >= date_from)
        if date_to:
            stmt = stmt.where(IncomeScheduleModel.expected_date <= date_to)
        return list((await self._session.execute(stmt.order_by(IncomeScheduleModel.expected_date.asc()))).scalars().all())

    async def update_schedule(self, schedule_id: uuid.UUID, user_id: uuid.UUID, **kwargs: object) -> IncomeScheduleModel | None:
        schedule = await self.get_schedule_by_id(schedule_id, user_id)
        if schedule is None:
            return None
        for k, v in kwargs.items():
            if hasattr(schedule, k):
                setattr(schedule, k, v)
        await self._session.flush()
        await self._session.refresh(schedule)
        return schedule

    async def delete_schedule(self, schedule_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        from datetime import UTC, datetime
        schedule = await self.get_schedule_by_id(schedule_id, user_id)
        if schedule is None:
            return False
        schedule.deleted_at = datetime.now(UTC)
        await self._session.flush()
        return True

    async def get_upcoming_schedules(self, user_id: uuid.UUID, days_ahead: int = 30) -> list[IncomeScheduleModel]:
        from datetime import date as date_type, timedelta
        cutoff = date_type.today() + timedelta(days=days_ahead)
        stmt = select(IncomeScheduleModel).where(IncomeScheduleModel.user_id == user_id,
            IncomeScheduleModel.status.in_(["projected", "expected"]),
            IncomeScheduleModel.expected_date <= cutoff, IncomeScheduleModel.deleted_at.is_(None)
        ).order_by(IncomeScheduleModel.expected_date.asc())
        return list((await self._session.execute(stmt)).scalars().all())

    async def get_projected_income(self, user_id: uuid.UUID, months: int = 6) -> dict:
        from decimal import Decimal
        from datetime import date as date_type, timedelta
        cutoff = date_type.today() + timedelta(days=months * 30)
        stmt = select(IncomeScheduleModel).where(IncomeScheduleModel.user_id == user_id,
            IncomeScheduleModel.status.in_(["projected", "expected"]),
            IncomeScheduleModel.expected_date <= cutoff, IncomeScheduleModel.deleted_at.is_(None)
        ).order_by(IncomeScheduleModel.expected_date.asc())
        schedules = list((await self._session.execute(stmt)).scalars().all())
        monthly, total = {}, Decimal("0")
        for s in schedules:
            key = s.expected_date.strftime("%Y-%m")
            monthly[key] = monthly.get(key, Decimal("0")) + s.amount
            total += s.amount
        return {"total_projected": str(total), "months": months,
            "monthly_breakdown": {k: str(v) for k, v in sorted(monthly.items())}, "schedule_count": len(schedules)}
