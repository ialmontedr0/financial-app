from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.repositories.credit_purchase_repository import CreditPurchaseRepository
from app.middleware.error_handler import NotFoundError


class MarkInstallmentPaidUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = CreditPurchaseRepository(session)

    async def execute(
        self,
        user_id: uuid.UUID,
        purchase_id: uuid.UUID,
        installment_id: uuid.UUID,
    ) -> dict:
        purchase = await self._repo.get(purchase_id, user_id)
        if not purchase:
            raise NotFoundError("Compra a credito no encontrada")

        entry = await self._repo.mark_installment_paid(installment_id)
        if not entry:
            raise NotFoundError("Cuota no encontrada")

        paid_total = sum(inst.amount for inst in purchase.installments if inst.status == "paid")
        purchase = await self._repo.update(purchase, total_paid=paid_total)

        all_paid = all(inst.status == "paid" for inst in purchase.installments)
        if all_paid:
            purchase = await self._repo.update(purchase, status="completed")

        return {
            "id": str(entry.id),
            "installment_number": entry.installment_number,
            "status": entry.status,
            "paid_at": entry.paid_at.isoformat() if entry.paid_at else None,
            "purchase_status": purchase.status,
        }
