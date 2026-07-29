from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.repositories.credit_purchase_repository import CreditPurchaseRepository
from app.middleware.error_handler import NotFoundError


class UpdateCreditPurchaseUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = CreditPurchaseRepository(session)

    async def execute(
        self, user_id: uuid.UUID, purchase_id: uuid.UUID, data: dict
    ) -> dict:
        purchase = await self._repo.get(purchase_id, user_id)
        if not purchase:
            raise NotFoundError("Compra a credito no encontrada")

        allowed = {
            "item_name", "store_name", "description", "notes",
            "status", "annual_interest_rate",
        }
        update_kwargs = {k: v for k, v in data.items() if k in allowed and v is not None}
        if not update_kwargs:
            raise NotFoundError("No hay campos validos para actualizar")

        purchase = await self._repo.update(purchase, **update_kwargs)
        return {"id": str(purchase.id), "status": "updated"}
