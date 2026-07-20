"""Use case: Create income from a pre-configured source with defaults."""

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


class CreateFromSourceUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._tx_repo = TransactionRepository(session)
        self._income_repo = IncomeRepository(session)

    async def execute(
        self,
        user_id: uuid.UUID,
        source_id: uuid.UUID,
        *,
        amount: float | None = None,
        effective_date: date | None = None,
        description: str | None = None,
        status: str = "completed",
        notes: str | None = None,
        tags: list[str] | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> dict:
        from datetime import date as date_type
        from decimal import Decimal

        from app.middleware.error_handler import NotFoundError, ValidationError

        source = await self._income_repo.get_source_by_id(source_id, user_id)
        if source is None:
            raise NotFoundError("IncomeSource")

        account_id = source.default_account_id
        category_id = source.default_category_id
        if not account_id:
            raise ValidationError("IncomeSource no tiene account por defecto configurado")

        final_amount = float(amount) if amount is not None else float(source.default_amount or 0)
        if final_amount <= 0:
            raise ValidationError("amount debe ser mayor que 0")

        ed = effective_date or date_type.today()
        tx_desc = description or f"Ingreso de {source.name}"

        tx = await self._tx_repo.create(
            user_id,
            account_id=account_id,
            category_id=category_id,
            transaction_type="income",
            status=status,
            amount=Decimal(str(final_amount)),
            currency_code=source.default_currency or "DOP",
            description=tx_desc,
            effective_date=ed,
            notes=notes,
            source="source",
        )

        if status == "completed":
            await self._tx_repo.update_account_balance(account_id, Decimal(str(final_amount)), "add")

        income = await self._income_repo.create_income(
            user_id,
            transaction_id=tx.id,
            income_type=source.income_type or "other",
            income_status="received" if status == "completed" else "pending",
            stability=source.stability or "fixed",
            income_source_id=source_id,
            employer_name=source.name,
            effective_date=ed,
            notes=notes,
        )

        await self._income_repo.increment_source_stats(source_id, Decimal(str(final_amount)))

        await self._tx_repo.create_audit_log(
            tx_id=tx.id,
            user_id=user_id,
            action="created_from_source",
            changes={"source_id": str(source_id), "amount": str(final_amount)},
            ip_address=ip_address,
            user_agent=user_agent,
        )

        if tags:
            await self._tx_repo.add_tags(tx.id, user_id, tags)

        await self._session.refresh(tx)
        tag_models = await self._tx_repo.get_tags(tx.id)

        return {
            "id": str(income.id),
            "transaction_id": str(tx.id),
            "account_id": str(tx.account_id),
            "amount": str(tx.amount),
            "currency_code": tx.currency_code,
            "description": tx.description,
            "effective_date": tx.effective_date.isoformat() if tx.effective_date else None,
            "source_id": str(source_id),
            "source_name": source.name,
            "income_type": income.income_type,
            "tags": [t.tag_name for t in tag_models],
            "created_at": tx.created_at.isoformat() if tx.created_at else None,
        }
