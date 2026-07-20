"""Use case: Create expense (wraps transaction creation with expense context)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.expense_repository import ExpenseRepository
from app.infrastructure.repositories.transaction_repository import TransactionRepository

if TYPE_CHECKING:
    import uuid
    from datetime import date

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class CreateExpenseUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._tx_repo = TransactionRepository(session)
        self._expense_repo = ExpenseRepository(session)

    async def execute(
        self,
        user_id: uuid.UUID,
        *,
        account_id: uuid.UUID,
        amount: float,
        currency_code: str,
        description: str,
        effective_date: date,
        category_id: uuid.UUID | None = None,
        subcategory_id: uuid.UUID | None = None,
        status: str = "completed",
        notes: str | None = None,
        source: str = "manual",
        tags: list[str] | None = None,
        template_id: uuid.UUID | None = None,
        service_id: uuid.UUID | None = None,
        subscription_id: uuid.UUID | None = None,
        credit_card_id: uuid.UUID | None = None,
        priority: str = "normal",
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> dict:
        from app.middleware.error_handler import NotFoundError, ValidationError

        # Validate expense method
        if template_id:
            source = "template"
        elif source not in ("manual", "template", "import", "recurring", "auto"):
            raise ValidationError(f"source no valido: {source}")

        # Validate priority
        valid_priorities = {"low", "normal", "high", "critical"}
        if priority not in valid_priorities:
            raise ValidationError(
                f"priority no valido: {priority}. Soportado: {', '.join(sorted(valid_priorities))}"
            )

        # Validate service exists if provided
        if service_id:
            service = await self._expense_repo.get_service_by_id(service_id, user_id)
            if service is None:
                raise NotFoundError("Service")
            # Auto-set category from service if not provided
            if not category_id and service.category_id:
                category_id = service.category_id

        # Validate subscription exists if provided
        if subscription_id:
            sub = await self._expense_repo.get_subscription_by_id(subscription_id, user_id)
            if sub is None:
                raise NotFoundError("Subscription")

        # Create the transaction via the transaction repository
        tx = await self._tx_repo.create(
            user_id,
            account_id=account_id,
            category_id=category_id,
            subcategory_id=subcategory_id,
            transaction_type="expense",
            status=status,
            amount=amount,
            currency_code=currency_code,
            description=str(description).strip(),
            notes=notes,
            effective_date=effective_date,
            source=source,
        )

        # Update balance if completed
        from decimal import Decimal

        if status == "completed":
            await self._tx_repo.update_account_balance(account_id, Decimal(str(amount)), "subtract")

        # Audit
        changes = {"initial": {"amount": str(amount), "source": source, "priority": priority}}
        if service_id:
            changes["service_id"] = str(service_id)
        if subscription_id:
            changes["subscription_id"] = str(subscription_id)
        if credit_card_id:
            changes["credit_card_id"] = str(credit_card_id)

        await self._tx_repo.create_audit_log(
            tx_id=tx.id,
            user_id=user_id,
            action="created",
            changes=changes,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        # Tags
        if tags:
            await self._tx_repo.add_tags(tx.id, user_id, tags)

        # Template usage tracking
        if template_id:
            await self._expense_repo.increment_template_usage(template_id)

        # Refresh and return
        await self._session.refresh(tx)
        tag_models = await self._tx_repo.get_tags(tx.id)

        return {
            "id": str(tx.id),
            "account_id": str(tx.account_id),
            "category_id": str(tx.category_id) if tx.category_id else None,
            "subcategory_id": str(tx.subcategory_id) if tx.subcategory_id else None,
            "transaction_type": tx.transaction_type,
            "status": tx.status,
            "amount": str(tx.amount),
            "currency_code": tx.currency_code,
            "description": tx.description,
            "notes": tx.notes,
            "effective_date": tx.effective_date.isoformat() if tx.effective_date else None,
            "source": tx.source,
            "tags": [t.tag_name for t in tag_models],
            "created_at": tx.created_at.isoformat() if tx.created_at else None,
            "priority": priority,
            "service_id": str(service_id) if service_id else None,
            "subscription_id": str(subscription_id) if subscription_id else None,
            "credit_card_id": str(credit_card_id) if credit_card_id else None,
        }
