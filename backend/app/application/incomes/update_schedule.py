"""Use case: Update an income schedule."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog

from app.infrastructure.repositories.income_repository import IncomeRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class UpdateScheduleUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = IncomeRepository(session)

    async def execute(
        self,
        user_id: uuid.UUID,
        schedule_id: uuid.UUID,
        *,
        changes: dict[str, Any],
    ) -> dict:
        from app.middleware.error_handler import NotFoundError, ValidationError

        schedule = await self._repo.get_schedule_by_id(schedule_id, user_id)
        if schedule is None:
            raise NotFoundError("IncomeSchedule")

        allowed_fields = {"description", "amount", "currency_code", "account_id", "expected_date", "income_source_id", "status", "frequency", "projection_method", "notes"}

        if "status" in changes:
            valid_statuses = {"projected", "expected", "received", "overdue", "cancelled"}
            if changes["status"] not in valid_statuses:
                raise ValidationError(f"status no valido: {changes['status']}")

        if "amount" in changes and float(changes["amount"]) <= 0:
            raise ValidationError("amount debe ser mayor que 0")

        filtered = {k: v for k, v in changes.items() if k in allowed_fields}
        if not filtered:
            return {"message": "No changes detected"}

        updated = await self._repo.update_schedule(schedule_id, user_id, **filtered)
        if updated is None:
            raise NotFoundError("IncomeSchedule")

        return {
            "id": str(updated.id),
            "description": updated.description,
            "amount": str(updated.amount),
            "currency_code": updated.currency_code,
            "account_id": str(updated.account_id),
            "expected_date": updated.expected_date.isoformat(),
            "status": updated.status,
            "frequency": updated.frequency,
            "income_source_id": str(updated.income_source_id) if updated.income_source_id else None,
            "projection_method": updated.projection_method,
            "notes": updated.notes,
            "updated_at": updated.updated_at.isoformat() if updated.updated_at else None,
        }
