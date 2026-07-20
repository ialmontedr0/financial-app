"""Use case: Soft-delete a subscription."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.expense_repository import ExpenseRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class DeleteSubscriptionUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = ExpenseRepository(session)

    async def execute(self, user_id: uuid.UUID, subscription_id: uuid.UUID) -> dict:
        from app.middleware.error_handler import NotFoundError

        deleted = await self._repo.delete_subscription(subscription_id, user_id)
        if not deleted:
            raise NotFoundError("Subscription")

        return {"id": str(subscription_id), "message": "Subscription eliminada exitosamente"}
