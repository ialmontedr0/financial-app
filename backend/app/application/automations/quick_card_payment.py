"""Use case: Quick setup auto card payment."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class QuickCardPaymentUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(
        self,
        user_id: uuid.UUID,
        card_id: uuid.UUID,
        payment_account_id: uuid.UUID,
        payment_type: str = "full",
        days_before_due: int = 3,
        name: str | None = None,
    ) -> dict:
        from app.infrastructure.repositories.automation_repository import (
            AutomationRepository,
        )

        repo = AutomationRepository(self._session)
        rule_name = name or f"Pago automatico tarjeta ({payment_type})"

        rule = await repo.create_rule(
            user_id=user_id,
            name=rule_name,
            description=f"Pago {payment_type} de tarjeta {days_before_due} dias antes del vencimiento",
            trigger_type="bill_due_soon",
            action_type="pay_credit_card",
            trigger_conditions={
                "card_id": str(card_id),
                "days_before_due": days_before_due,
            },
            action_params={
                "card_id": str(card_id),
                "payment_account_id": str(payment_account_id),
                "payment_type": payment_type,
            },
        )

        return {
            "id": str(rule.id),
            "name": rule.name,
            "message": "Pago automatico de tarjeta configurado",
        }
