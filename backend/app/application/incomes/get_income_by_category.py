"""Use case: Get income breakdown by category."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog
from sqlalchemy import func, select

from app.infrastructure.models.category import CategoryModel
from app.infrastructure.models.income import IncomeModel
from app.infrastructure.models.transaction import TransactionModel

if TYPE_CHECKING:
    import uuid
    from datetime import date

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class GetIncomeByCategoryUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(
        self,
        user_id: uuid.UUID,
        *,
        date_from: date,
        date_to: date,
    ) -> dict:
        from decimal import Decimal

        from app.middleware.error_handler import ValidationError

        if date_from > date_to:
            raise ValidationError("date_from debe ser menor o igual que date_to")

        stmt = (
            select(
                CategoryModel.id.label("category_id"),
                CategoryModel.name.label("category_name"),
                func.count(IncomeModel.id).label("count"),
                func.sum(TransactionModel.amount).label("total"),
            )
            .join(TransactionModel, IncomeModel.transaction_id == TransactionModel.id)
            .join(CategoryModel, TransactionModel.category_id == CategoryModel.id, isouter=True)
            .where(
                IncomeModel.user_id == user_id,
                IncomeModel.deleted_at.is_(None),
                IncomeModel.effective_date >= date_from,
                IncomeModel.effective_date <= date_to,
            )
            .group_by(CategoryModel.id, CategoryModel.name)
            .order_by(func.sum(TransactionModel.amount).desc())
        )

        rows = (await self._session.execute(stmt)).all()

        grand_total = Decimal("0")
        items = []
        for r in rows:
            total = Decimal(str(r.total or 0))
            grand_total += total
            items.append({
                "category_id": str(r.category_id) if r.category_id else None,
                "category_name": r.category_name or "Sin categoria",
                "count": r.count,
                "total": str(total),
            })

        for item in items:
            t = Decimal(item["total"])
            item["percentage"] = str(round(float(t / grand_total * 100), 2)) if grand_total > 0 else "0"

        return {"categories": items, "grand_total": str(grand_total), "total_categories": len(items)}
