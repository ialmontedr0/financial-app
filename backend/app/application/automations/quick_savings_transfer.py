"""Use case: Quick setup auto-savings automation."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class QuickSavingsTransferUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(
        self,
        user_id: uuid.UUID,
        source_account_id: uuid.UUID,
        target_account_id: uuid.UUID,
        amount: float,
        amount_type: str = "fixed",
        trigger_type: str = "income_received",
        trigger_conditions: dict | None = None,
        name: str | None = None,
    ) -> dict:
        from app.infrastructure.repositories.automation_repository import (
            AutomationRepository,
        )

        repo = AutomationRepository(self._session)
        rule_name = name or f"Ahorro automatico {amount_type}"

        rule = await repo.create_rule(
            user_id=user_id,
            name=rule_name,
            description=f"Transfiere {amount} automaticamente ({amount_type})",
            trigger_type=trigger_type,
            action_type="transfer",
            trigger_conditions=trigger_conditions or {"min_amount": amount * 2},
            action_params={
                "source_account_id": str(source_account_id),
                "target_account_id": str(target_account_id),
                "amount": amount,
                "amount_type": amount_type,
            },
        )

        return {
            "id": str(rule.id),
            "name": rule.name,
            "message": "Ahorro automatico configurado",
        }
