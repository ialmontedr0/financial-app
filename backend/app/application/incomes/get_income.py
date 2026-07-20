"""Use case: Get a single income by ID."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.income_repository import IncomeRepository
from app.infrastructure.repositories.transaction_repository import TransactionRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class GetIncomeUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._tx_repo = TransactionRepository(session)
        self._income_repo = IncomeRepository(session)

    async def execute(self, user_id: uuid.UUID, income_id: uuid.UUID) -> dict:
        from app.middleware.error_handler import NotFoundError, ValidationError

        income = await self._income_repo.get_income_by_id(income_id, user_id)
        if income is None:
            raise NotFoundError("Income")

        tx = await self._tx_repo.get_by_id(income.transaction_id, user_id)
        if tx is None:
            raise NotFoundError("Transaction")
        if tx.transaction_type != "income":
            raise ValidationError("Transaction is not an income")

        tags = await self._tx_repo.get_tags(tx.id)
        attachments = await self._tx_repo.list_attachments(tx.id)

        source_name = None
        if income.income_source_id:
            source_model = await self._income_repo.get_source_by_id(income.income_source_id, user_id)
            source_name = source_model.name if source_model else None

        return {
            "id": str(income.id),
            "transaction_id": str(tx.id),
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
            "tags": [t.tag_name for t in tags],
            "attachments": [
                {
                    "id": str(a.id),
                    "original_filename": a.original_filename,
                    "mime_type": a.mime_type,
                    "file_size": a.file_size,
                    "created_at": a.created_at.isoformat() if a.created_at else None,
                }
                for a in attachments
            ],
            "income_type": income.income_type,
            "income_status": income.income_status,
            "stability": income.stability,
            "income_source_id": str(income.income_source_id) if income.income_source_id else None,
            "income_source_name": source_name,
            "employer_name": income.employer_name,
            "employer_tax_id": income.employer_tax_id,
            "gross_amount": str(income.gross_amount) if income.gross_amount else None,
            "tax_withheld": str(income.tax_withheld) if income.tax_withheld else None,
            "net_amount": str(income.net_amount) if income.net_amount else None,
            "frequency": income.frequency,
            "created_at": tx.created_at.isoformat() if tx.created_at else None,
            "updated_at": tx.updated_at.isoformat() if tx.updated_at else None,
        }
