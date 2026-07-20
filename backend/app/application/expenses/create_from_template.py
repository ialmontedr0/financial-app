"""Use case: Create an expense from a template (apply template defaults)."""

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


class CreateFromTemplateUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._tx_repo = TransactionRepository(session)
        self._expense_repo = ExpenseRepository(session)

    async def execute(
        self,
        user_id: uuid.UUID,
        template_id: uuid.UUID,
        *,
        effective_date: date,
        amount: float | None = None,
        account_id: uuid.UUID | None = None,
        notes: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> dict:
        from app.middleware.error_handler import NotFoundError

        template = await self._expense_repo.get_template_by_id(template_id, user_id)
        if template is None:
            raise NotFoundError("Template")

        # Use template defaults, allow overrides
        final_amount = amount or template.default_amount
        final_account_id = account_id or template.default_account_id
        if final_account_id is None:
            from app.middleware.error_handler import ValidationError

            raise ValidationError("account_id es requerido (template no tiene default_account_id)")

        tx = await self._tx_repo.create(
            user_id,
            account_id=final_account_id,
            category_id=template.default_category_id,
            subcategory_id=template.default_subcategory_id,
            transaction_type="expense",
            status="completed",
            amount=final_amount,
            currency_code="DOP",
            description=template.name,
            notes=notes or template.default_notes,
            effective_date=effective_date,
            source="template",
        )

        await self._tx_repo.update_account_balance(final_account_id, final_amount, "subtract")

        await self._expense_repo.increment_template_usage(template_id)

        await self._tx_repo.create_audit_log(
            tx_id=tx.id,
            user_id=user_id,
            action="created",
            changes={"template_id": str(template_id), "amount": str(final_amount)},
            ip_address=ip_address,
            user_agent=user_agent,
        )

        if template.default_tags:
            await self._tx_repo.add_tags(tx.id, user_id, template.default_tags)

        return {
            "id": str(tx.id),
            "template_id": str(template_id),
            "amount": str(tx.amount),
            "description": tx.description,
            "effective_date": tx.effective_date.isoformat() if tx.effective_date else None,
            "source": tx.source,
            "created_at": tx.created_at.isoformat() if tx.created_at else None,
        }
