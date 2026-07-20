"""Use case: Create a scheduled/income projection."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.income_repository import IncomeRepository

if TYPE_CHECKING:
    import uuid
    from datetime import date

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class CreateScheduleUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = IncomeRepository(session)

    async def execute(
        self,
        user_id: uuid.UUID,
        *,
        description: str,
        amount: float,
        currency_code: str = "DOP",
        account_id: uuid.UUID,
        expected_date: date,
        income_source_id: uuid.UUID | None = None,
        status: str = "projected",
        frequency: str | None = None,
        projection_method: str | None = None,
        notes: str | None = None,
    ) -> dict:
        from decimal import Decimal

        from app.middleware.error_handler import ValidationError

        if not description or not description.strip():
            raise ValidationError("description es requerido")
        if amount <= 0:
            raise ValidationError("amount debe ser mayor que 0")

        valid_statuses = {"projected", "expected", "received", "overdue", "cancelled"}
        if status not in valid_statuses:
            raise ValidationError(f"status no valido: {status}. Soportado: {', '.join(sorted(valid_statuses))}")

        schedule = await self._repo.create_schedule(
            user_id,
            description=str(description).strip(),
            amount=Decimal(str(amount)),
            currency_code=currency_code,
            account_id=account_id,
            expected_date=expected_date,
            income_source_id=income_source_id,
            status=status,
            frequency=frequency,
            projection_method=projection_method,
            notes=notes,
        )

        return {
            "id": str(schedule.id),
            "description": schedule.description,
            "amount": str(schedule.amount),
            "currency_code": schedule.currency_code,
            "account_id": str(schedule.account_id),
            "expected_date": schedule.expected_date.isoformat(),
            "status": schedule.status,
            "frequency": schedule.frequency,
            "income_source_id": str(schedule.income_source_id) if schedule.income_source_id else None,
            "projection_method": schedule.projection_method,
            "notes": schedule.notes,
            "created_at": schedule.created_at.isoformat() if schedule.created_at else None,
        }
