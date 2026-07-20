"""Use case: List expenses with advanced filtering."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.transaction_repository import TransactionRepository

if TYPE_CHECKING:
    import uuid
    from datetime import date

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class ListExpensesUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = TransactionRepository(session)

    async def execute(
        self,
        user_id: uuid.UUID,
        *,
        status: str | None = None,
        category_id: str | None = None,
        subcategory_id: str | None = None,
        account_id: str | None = None,
        tag: str | None = None,
        min_amount: float | None = None,
        max_amount: float | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        source: str | None = None,
        search: str | None = None,
        credit_card_id: uuid.UUID | None = None,  # noqa: ARG002
        sort_by: str = "effective_date",
        sort_order: str = "desc",
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        import uuid as uuid_mod

        # Always filter for expenses only
        cat_uuid = uuid_mod.UUID(category_id) if category_id else None
        sub_uuid = uuid_mod.UUID(subcategory_id) if subcategory_id else None
        acc_uuid = uuid_mod.UUID(account_id) if account_id else None

        txs, total = await self._repo.list_by_user(
            user_id,
            transaction_type="expense",
            status=status,
            category_id=cat_uuid,
            subcategory_id=sub_uuid,
            account_id=acc_uuid,
            tag=tag,
            min_amount=min_amount,
            max_amount=max_amount,
            date_from=date_from,
            date_to=date_to,
            source=source,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            page_size=page_size,
        )

        items = []
        for tx in txs:
            tags_list = [t.tag_name for t in tx.tags] if hasattr(tx, "tags") and tx.tags else []
            items.append(
                {
                    "id": str(tx.id),
                    "account_id": str(tx.account_id),
                    "category_id": str(tx.category_id) if tx.category_id else None,
                    "subcategory_id": str(tx.subcategory_id) if tx.subcategory_id else None,
                    "transaction_type": tx.transaction_type,
                    "status": tx.status,
                    "amount": str(tx.amount),
                    "currency_code": tx.currency_code,
                    "description": tx.description,
                    "notes": tx.notes,
                    "effective_date": tx.effective_date.isoformat() if tx.effective_date else None,
                    "source": tx.source,
                    "tags": tags_list,
                    "created_at": tx.created_at.isoformat() if tx.created_at else None,
                }
            )

        return {
            "expenses": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
        }
