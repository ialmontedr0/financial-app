"""Use case: Mark a service as paid for current month and create expense record."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.expense_repository import ExpenseRepository
from app.infrastructure.repositories.transaction_repository import TransactionRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class MarkServicePaidUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._tx_repo = TransactionRepository(session)
        self._expense_repo = ExpenseRepository(session)

    async def execute(
        self,
        user_id: uuid.UUID,
        service_id: uuid.UUID,
        *,
        amount: float,
        account_id: uuid.UUID,
        effective_date: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> dict:
        from datetime import date as date_type
        from decimal import Decimal

        from app.middleware.error_handler import NotFoundError, ValidationError

        service = await self._expense_repo.get_service_by_id(service_id, user_id)
        if service is None:
            raise NotFoundError("Service")
        if not service.is_active:
            raise ValidationError("Service is not active")

        if amount <= 0:
            raise ValidationError("Amount must be > 0")

        ed = date_type.fromisoformat(effective_date) if effective_date else date_type.today()  # noqa: DTZ011

        # Idempotencia: el servicio ya fue pagado este periodo (mismo mes).
        # Evita doble-pago si el cliente reintenta la operación.
        if service.last_paid_at is not None:
            same_period = (
                service.frequency == "monthly"
                and service.last_paid_at.year == ed.year
                and service.last_paid_at.month == ed.month
            ) or (
                service.frequency == "annually"
                and service.last_paid_at.year == ed.year
            )
            if same_period:
                raise ValidationError(
                    f"El servicio '{service.name}' ya fue pagado para este periodo"
                )

        # Usar la moneda de la cuenta si existe; fallback a DOP (A4.10).
        account = await self._tx_repo.get_account_by_id(account_id, user_id)
        currency_code = (
            account.currency_code
            if account is not None and getattr(account, "currency_code", None)
            else "DOP"
        )

        # Create expense linked to service
        tx = await self._tx_repo.create(
            user_id,
            account_id=account_id,
            category_id=service.category_id,
            transaction_type="expense",
            status="completed",
            amount=amount,
            currency_code=currency_code,
            description=f"Pago: {service.name}",
            effective_date=ed,
            source="manual",
        )

        await self._tx_repo.update_account_balance(account_id, Decimal(str(amount)), "subtract")

        # Mark service as paid
        await self._expense_repo.update_service(
            service_id, user_id, payment_status="paid", last_paid_at=ed
        )

        await self._tx_repo.create_audit_log(
            tx_id=tx.id,
            user_id=user_id,
            action="created",
            changes={
                "service_id": str(service_id),
                "amount": str(amount),
                "service_name": service.name,
            },
            ip_address=ip_address,
            user_agent=user_agent,
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
            "transaction_id": str(tx.id),
            "service_id": str(service_id),
            "service_name": service.name,
            "amount": str(tx.amount),
            "effective_date": tx.effective_date.isoformat() if tx.effective_date else None,
            "is_paid_current_month": True,
            "created_at": tx.created_at.isoformat() if tx.created_at else None,
        }
