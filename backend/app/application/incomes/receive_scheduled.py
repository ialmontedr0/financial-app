"""Use case: Receive a scheduled income (convert projection to real income)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.income_repository import IncomeRepository
from app.infrastructure.repositories.transaction_repository import TransactionRepository

if TYPE_CHECKING:
    import uuid
    from datetime import date

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class ReceiveScheduledUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._tx_repo = TransactionRepository(session)
        self._income_repo = IncomeRepository(session)

    async def execute(
        self,
        user_id: uuid.UUID,
        schedule_id: uuid.UUID,
        *,
        amount: float | None = None,
        effective_date: date | None = None,
        notes: str | None = None,
        tags: list[str] | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> dict:
        from decimal import Decimal

        from app.middleware.error_handler import NotFoundError, ValidationError

        schedule = await self._income_repo.get_schedule_by_id(schedule_id, user_id)
        if schedule is None:
            raise NotFoundError("IncomeSchedule")
        if schedule.status in ("received", "cancelled"):
            raise ValidationError(f"Schedule ya esta en status: {schedule.status}")

        final_amount = Decimal(str(amount)) if amount is not None else schedule.amount
        if final_amount <= 0:
            raise ValidationError("amount debe ser mayor que 0")

        ed = effective_date if effective_date is not None else schedule.expected_date

        tx = await self._tx_repo.create(
            user_id,
            account_id=schedule.account_id,
            transaction_type="income",
            status="completed",
            amount=final_amount,
            currency_code=schedule.currency_code,
            description=schedule.description,
            effective_date=ed,
            source="scheduled",
            notes=notes,
        )

        await self._tx_repo.update_account_balance(schedule.account_id, final_amount, "add")

        income = await self._income_repo.create_income(
            user_id,
            transaction_id=tx.id,
            income_type="other",
            income_status="received",
            stability="one_time",
            income_source_id=schedule.income_source_id,
            effective_date=ed,
            notes=notes,
        )

        from datetime import UTC, datetime
        await self._income_repo.update_schedule(schedule_id, user_id,
            status="received", received_transaction_id=tx.id,
            received_at=datetime.now(UTC))

        if schedule.income_source_id:
            await self._income_repo.increment_source_stats(schedule.income_source_id, final_amount)

        await self._tx_repo.create_audit_log(
            tx_id=tx.id,
            user_id=user_id,
            action="received_scheduled",
            changes={"schedule_id": str(schedule_id), "amount": str(final_amount)},
            ip_address=ip_address,
            user_agent=user_agent,
        )

        if tags:
            await self._tx_repo.add_tags(tx.id, user_id, tags)

        tag_models = await self._tx_repo.get_tags(tx.id)

        return {
            "id": str(income.id),
            "transaction_id": str(tx.id),
            "schedule_id": str(schedule_id),
            "amount": str(tx.amount),
            "currency_code": tx.currency_code,
            "description": tx.description,
            "effective_date": tx.effective_date.isoformat() if tx.effective_date else None,
            "tags": [t.tag_name for t in tag_models],
            "created_at": tx.created_at.isoformat() if tx.created_at else None,
        }
