"""Use case: Quick setup balance-based transfer."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class QuickBalanceTransferUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(
        self,
        user_id: uuid.UUID,
        source_account_id: uuid.UUID,
        target_account_id: uuid.UUID,
        threshold: float,
        direction: str = "above",
        percent_to_transfer: float = 50.0,
        name: str | None = None,
    ) -> dict:
        from app.infrastructure.repositories.automation_repository import (
            AutomationRepository,
        )

        repo = AutomationRepository(self._session)
        rule_name = name or f"Transferencia por saldo ({direction} {threshold})"

        rule = await repo.create_rule(
            user_id=user_id,
            name=rule_name,
            description=f"Transfiere {percent_to_transfer}% cuando saldo {'supera' if direction == 'above' else 'baja'} {threshold}",
            trigger_type="balance_threshold",
            action_type="transfer",
            trigger_conditions={
                "account_id": str(source_account_id),
                "threshold": threshold,
                "direction": direction,
            },
            action_params={
                "source_account_id": str(source_account_id),
                "target_account_id": str(target_account_id),
                "amount": percent_to_transfer,
                "amount_type": "percent_of_balance",
            },
        )

        return {
            "id": str(rule.id),
            "name": rule.name,
            "message": "Transferencia por saldo configurada",
        }
