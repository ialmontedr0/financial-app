"""Use case: List transactions with filters and pagination."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.transaction_repository import TransactionRepository

if TYPE_CHECKING:
    import uuid
    from datetime import date

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class ListTransactionsUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = TransactionRepository(session)

    async def execute(self, user_id: uuid.UUID, *, transaction_type: str | None = None,
        status: str | None = None, category_id: uuid.UUID | None = None,
        subcategory_id: uuid.UUID | None = None, account_id: uuid.UUID | None = None,
        tag: str | None = None, min_amount: float | None = None, max_amount: float | None = None,
        date_from: date | None = None, date_to: date | None = None, source: str | None = None,
        search: str | None = None, sort_by: str = "effective_date", sort_order: str = "desc",
        page: int = 1, page_size: int = 20,
    ) -> dict:
        from decimal import Decimal

        min_amt = Decimal(str(min_amount)) if min_amount is not None else None
        max_amt = Decimal(str(max_amount)) if max_amount is not None else None

        txs, total = await self._repo.list_by_user(user_id, transaction_type=transaction_type, status=status,
            category_id=category_id, subcategory_id=subcategory_id, account_id=account_id, tag=tag,
            min_amount=min_amt, max_amount=max_amt, date_from=date_from, date_to=date_to,
            source=source, search=search, sort_by=sort_by, sort_order=sort_order, page=page, page_size=page_size,
        )

        items: list[dict] = []
        for tx in txs:
            tags = await self._repo.get_tags(tx.id)
            items.append({
                "id": str(tx.id), "account_id": str(tx.account_id),
                "category_id": str(tx.category_id) if tx.category_id else None,
                "subcategory_id": str(tx.subcategory_id) if tx.subcategory_id else None,
                "transaction_type": tx.transaction_type, "status": tx.status,
                "amount": str(tx.amount), "currency_code": tx.currency_code,
                "description": tx.description,
                "effective_date": tx.effective_date.isoformat() if tx.effective_date else None,
                "source": tx.source, "tags": [t.tag_name for t in tags],
                "created_at": tx.created_at.isoformat() if tx.created_at else None,
            })

        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
        return {"transactions": items, "total": total, "page": page, "page_size": page_size, "total_pages": total_pages}
