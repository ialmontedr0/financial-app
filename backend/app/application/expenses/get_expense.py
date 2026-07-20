from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.expense_repository import ExpenseRepository
from app.infrastructure.repositories.transaction_repository import TransactionRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class GetExpenseUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._tx_repo = TransactionRepository(session)
        self._expense_repo = ExpenseRepository(session)

    async def execute(self, user_id: uuid.UUID, expense_id: uuid.UUID) -> dict:
        from app.middleware.error_handler import NotFoundError, ValidationError

        tx = await self._tx_repo.get_by_id(expense_id, user_id)
        if tx is None:
            raise NotFoundError("Expense")
        if tx.transaction_type != "expense":
            raise ValidationError("Transaction is not an expense")

        tags = await self._tx_repo.get_tags(tx.id)
        attachments = await self._tx_repo.list_attachments(tx.id)

        # Resolve linked entities if present
        service = None
        if hasattr(tx, "service_id") and getattr(tx, "service_id", None):
            from app.infrastructure.models.expense_service import ExpenseServiceModel

            svc_stmt = (
                __import__("sqlalchemy")
                .select(ExpenseServiceModel)
                .where(
                    ExpenseServiceModel.id == tx.service_id,
                )
            )
            svc_result = await self._session.execute(svc_stmt)
            service = svc_result.scalar_one_or_none()

        subscription = None
        if hasattr(tx, "subscription_id") and getattr(tx, "subscription_id", None):
            from app.infrastructure.models.subscription import SubscriptionModel

            sub_stmt = (
                __import__("sqlalchemy")
                .select(SubscriptionModel)
                .where(
                    SubscriptionModel.id == tx.subscription_id,
                )
            )
            sub_result = await self._session.execute(sub_stmt)
            subscription = sub_result.scalar_one_or_none()

        return {
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
            "transfer_id": str(tx.transfer_id) if tx.transfer_id else None,
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
            "service_id": str(service.id) if service else None,
            "service_name": service.name if service else None,
            "subscription_id": str(subscription.id) if subscription else None,
            "subscription_name": subscription.name if subscription else None,
            "created_at": tx.created_at.isoformat() if tx.created_at else None,
            "updated_at": tx.updated_at.isoformat() if tx.updated_at else None,
        }
