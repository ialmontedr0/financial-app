"""Use case: Create a recurring transaction pattern."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.transaction_repository import TransactionRepository

if TYPE_CHECKING:
    import uuid
    from datetime import date

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class CreateRecurringUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = TransactionRepository(session)

    async def execute(self, user_id: uuid.UUID, *, account_id: uuid.UUID, transaction_type: str,
        amount: float, currency_code: str, description: str, frequency: str,
        start_date: date, interval: int = 1, category_id: uuid.UUID | None = None,
        subcategory_id: uuid.UUID | None = None, notes: str | None = None,
        end_date: date | None = None, max_executions: int | None = None,
    ) -> dict:
        from decimal import Decimal

        from app.domain.transactions.value_objects import RecurrenceFrequency, TransactionType
        from app.middleware.error_handler import NotFoundError, ValidationError

        try:
            RecurrenceFrequency(frequency)
        except ValueError as e:
            raise ValidationError(str(e))  # noqa: B904
        try:
            TransactionType(transaction_type)
        except ValueError as e:
            raise ValidationError(str(e))  # noqa: B904
        if not description or not str(description).strip():
            raise ValidationError("description es requerido")
        try:
            amount_decimal = Decimal(str(amount))
            if amount_decimal <= 0:
                raise ValidationError("amount debe ser mayor a 0")
        except ValidationError:
            raise
        except Exception:
            raise ValidationError("amount invalido")  # noqa: B904

        account = await self._repo.get_account_by_id(account_id, user_id)
        if account is None:
            raise NotFoundError("Account")

        freq = RecurrenceFrequency(frequency)
        next_date = freq.calculate_next_date(start_date, interval)

        rec = await self._repo.create_recurring(user_id, account_id=account_id, category_id=category_id,
            subcategory_id=subcategory_id, transaction_type=transaction_type, amount=amount_decimal,
            currency_code=currency_code, description=str(description).strip(), notes=notes,
            frequency=frequency, interval=interval, start_date=start_date, end_date=end_date,
            next_execution_date=next_date, max_executions=max_executions, is_active=True,
        )

        return {"id": str(rec.id), "transaction_type": rec.transaction_type, "amount": str(rec.amount),
            "currency_code": rec.currency_code, "description": rec.description, "frequency": rec.frequency,
            "interval": rec.interval, "start_date": rec.start_date.isoformat(),
            "end_date": rec.end_date.isoformat() if rec.end_date else None,
            "next_execution_date": rec.next_execution_date.isoformat(), "max_executions": rec.max_executions,
            "execution_count": rec.execution_count, "is_active": rec.is_active,
            "created_at": rec.created_at.isoformat() if rec.created_at else None}
