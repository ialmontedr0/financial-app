"""Use case: Create a scheduled/income projection."""

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


class CreateScheduleUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = IncomeRepository(session)
        self._tx_repo = TransactionRepository(session)

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
        from datetime import UTC, datetime, date as date_type
        from decimal import Decimal

        from app.middleware.error_handler import ValidationError

        if not description or not description.strip():
            raise ValidationError("description es requerido")
        if amount <= 0:
            raise ValidationError("amount debe ser mayor que 0")

        valid_statuses = {"projected", "expected", "received", "overdue", "cancelled"}
        if status not in valid_statuses:
            raise ValidationError(
                f"status no valido: {status}. Soportado: {', '.join(sorted(valid_statuses))}"
            )

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

        # Auto-receive if the expected date is in the past
        today = date_type.today()
        if expected_date < today and status not in ("received", "cancelled"):
            final_amount = Decimal(str(amount))
            ed = expected_date

            tx = await self._tx_repo.create(
                user_id,
                account_id=account_id,
                transaction_type="income",
                status="completed",
                amount=final_amount,
                currency_code=currency_code,
                description=str(description).strip(),
                effective_date=ed,
                source="scheduled",
                notes=notes,
            )

            await self._tx_repo.update_account_balance(account_id, final_amount, "add")

            income = await self._repo.create_income(
                user_id,
                transaction_id=tx.id,
                income_type="other",
                income_status="received",
                stability="one_time",
                income_source_id=income_source_id,
                effective_date=ed,
                notes=notes,
            )

            await self._repo.update_schedule(
                schedule.id,
                user_id,
                status="received",
                received_transaction_id=tx.id,
                received_at=datetime.now(UTC),
            )

            if schedule.income_source_id:
                await self._repo.increment_source_stats(schedule.income_source_id, final_amount)

            await self._tx_repo.create_audit_log(
                tx_id=tx.id,
                user_id=user_id,
                action="auto_received_scheduled",
                changes={
                    "schedule_id": str(schedule.id),
                    "amount": str(final_amount),
                    "reason": "past_expected_date",
                },
                ip_address=None,
                user_agent=None,
            )

            from app.application.transactions.notifications import emit_transaction_notification

            await emit_transaction_notification(
                self._session,
                user_id,
                transaction_id=tx.id,
                account_id=tx.account_id,
                amount=f"{tx.amount}",
                currency_code=tx.currency_code,
                action="created",
            )

            return {
                "id": str(schedule.id),
                "description": schedule.description,
                "amount": str(schedule.amount),
                "currency_code": schedule.currency_code,
                "account_id": str(schedule.account_id),
                "expected_date": schedule.expected_date.isoformat(),
                "status": "received",
                "frequency": schedule.frequency,
                "income_source_id": str(schedule.income_source_id)
                if schedule.income_source_id
                else None,
                "projection_method": schedule.projection_method,
                "notes": schedule.notes,
                "created_at": schedule.created_at.isoformat() if schedule.created_at else None,
                "auto_received": True,
            }

        return {
            "id": str(schedule.id),
            "description": schedule.description,
            "amount": str(schedule.amount),
            "currency_code": schedule.currency_code,
            "account_id": str(schedule.account_id),
            "expected_date": schedule.expected_date.isoformat(),
            "status": schedule.status,
            "frequency": schedule.frequency,
            "income_source_id": str(schedule.income_source_id)
            if schedule.income_source_id
            else None,
            "projection_method": schedule.projection_method,
            "notes": schedule.notes,
            "created_at": schedule.created_at.isoformat() if schedule.created_at else None,
        }
