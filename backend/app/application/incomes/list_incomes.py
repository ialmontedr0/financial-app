"""Use case: List incomes with advanced filtering."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.income_repository import IncomeRepository

if TYPE_CHECKING:
    import uuid
    from datetime import date

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class ListIncomesUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = IncomeRepository(session)

    async def execute(
        self,
        user_id: uuid.UUID,
        *,
        income_type: str | None = None,
        income_status: str | None = None,
        stability: str | None = None,
        income_source_id: uuid.UUID | None = None,
        category_id: uuid.UUID | None = None,
        account_id: uuid.UUID | None = None,
        min_amount: float | None = None,
        max_amount: float | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        search: str | None = None,
        sort_by: str = "effective_date",
        sort_order: str = "desc",
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        incomes, total = await self._repo.list_incomes(
            user_id,
            income_type=income_type,
            income_status=income_status,
            stability=stability,
            income_source_id=income_source_id,
            category_id=category_id,
            account_id=account_id,
            min_amount=min_amount,
            max_amount=max_amount,
            date_from=date_from,
            date_to=date_to,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            page_size=page_size,
        )

        items = []
        for inc in incomes:
            items.append({
                "id": str(inc.id),
                "transaction_id": str(inc.transaction_id),
                "income_type": inc.income_type,
                "income_status": inc.income_status,
                "stability": inc.stability,
                "employer_name": inc.employer_name,
                "effective_date": inc.effective_date.isoformat() if inc.effective_date else None,
                "income_source_id": str(inc.income_source_id) if inc.income_source_id else None,
            })

        return {
            "incomes": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
        }
