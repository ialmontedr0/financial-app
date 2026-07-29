from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.repositories.credit_purchase_repository import CreditPurchaseRepository
from app.middleware.error_handler import NotFoundError


class GetCreditPurchaseUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = CreditPurchaseRepository(session)

    async def execute(self, user_id: uuid.UUID, purchase_id: uuid.UUID) -> dict:
        purchase = await self._repo.get(purchase_id, user_id)
        if not purchase:
            raise NotFoundError("Compra a credito no encontrada")

        paid = sum(1 for inst in purchase.installments if inst.status == "paid")
        installments = [
            {
                "id": str(inst.id),
                "installment_number": inst.installment_number,
                "due_date": inst.due_date.isoformat(),
                "amount": float(inst.amount),
                "principal_portion": float(inst.principal_portion),
                "interest_portion": float(inst.interest_portion),
                "balance_after": float(inst.balance_after),
                "status": inst.status,
                "paid_at": inst.paid_at.isoformat() if inst.paid_at else None,
            }
            for inst in purchase.installments
        ]

        return {
            "id": str(purchase.id),
            "item_name": purchase.item_name,
            "store_name": purchase.store_name,
            "description": purchase.description,
            "total_price": float(purchase.total_price),
            "down_payment": float(purchase.down_payment),
            "financed_amount": float(purchase.financed_amount),
            "annual_interest_rate": float(purchase.annual_interest_rate),
            "installment_count": purchase.installment_count,
            "installment_frequency": purchase.installment_frequency,
            "installment_amount": float(purchase.installment_amount),
            "calculation_method": purchase.calculation_method,
            "total_interest": float(purchase.total_interest),
            "total_paid": float(purchase.total_paid),
            "purchase_date": purchase.purchase_date.isoformat(),
            "first_due_date": purchase.first_due_date.isoformat(),
            "status": purchase.status,
            "notes": purchase.notes,
            "paid_installments": paid,
            "progress_pct": round(paid / purchase.installment_count * 100, 1) if purchase.installment_count > 0 else 0,
            "installments": installments,
            "created_at": purchase.created_at.isoformat() if purchase.created_at else None,
            "updated_at": purchase.updated_at.isoformat() if purchase.updated_at else None,
        }
