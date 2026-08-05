from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.repositories.credit_purchase_repository import CreditPurchaseRepository


class ListCreditPurchasesUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = CreditPurchaseRepository(session)

    async def execute(self, user_id: uuid.UUID, status: str | None = None) -> dict:
        purchases = await self._repo.list(user_id, status=status)
        items = []
        for p in purchases:
            paid = sum(1 for inst in p.installments if inst.status == "paid")
            items.append(
                {
                    "id": str(p.id),
                    "item_name": p.item_name,
                    "store_name": p.store_name,
                    "total_price": float(p.total_price),
                    "down_payment": float(p.down_payment),
                    "financed_amount": float(p.financed_amount),
                    "installment_amount": float(p.installment_amount),
                    "installment_count": p.installment_count,
                    "installment_frequency": p.installment_frequency,
                    "total_paid": float(p.total_paid),
                    "status": p.status,
                    "paid_installments": paid,
                    "total_installments": p.installment_count,
                    "purchase_date": p.purchase_date.isoformat(),
                    "created_at": p.created_at.isoformat() if p.created_at else None,
                }
            )
        return {"purchases": items, "total": len(items)}
