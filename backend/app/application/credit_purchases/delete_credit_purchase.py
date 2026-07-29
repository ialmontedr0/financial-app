from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.repositories.credit_purchase_repository import CreditPurchaseRepository
from app.middleware.error_handler import NotFoundError


class DeleteCreditPurchaseUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = CreditPurchaseRepository(session)

    async def execute(self, user_id: uuid.UUID, purchase_id: uuid.UUID) -> dict:
        purchase = await self._repo.get(purchase_id, user_id)
        if not purchase:
            raise NotFoundError("Compra a credito no encontrada")
        await self._repo.delete(purchase)
        return {"id": str(purchase_id), "status": "deleted"}
