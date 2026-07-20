"""Use case: Create income (wraps transaction creation with income context)."""

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


class CreateIncomeUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._tx_repo = TransactionRepository(session)
        self._income_repo = IncomeRepository(session)

    async def execute(
        self,
        user_id: uuid.UUID,
        *,
        account_id: uuid.UUID,
        amount: float,
        currency_code: str = "DOP",
        description: str,
        effective_date: date,
        category_id: uuid.UUID | None = None,
        subcategory_id: uuid.UUID | None = None,
        status: str = "completed",
        notes: str | None = None,
        source: str = "manual",
        tags: list[str] | None = None,
        income_type: str = "salary",
        income_status: str = "received",
        stability: str = "fixed",
        income_source_id: uuid.UUID | None = None,
        employer_name: str | None = None,
        employer_tax_id: str | None = None,
        gross_amount: float | None = None,
        tax_withheld: float | None = None,
        net_amount: float | None = None,
        frequency: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> dict:
        from decimal import Decimal

        from app.middleware.error_handler import NotFoundError, ValidationError

        valid_sources = {"manual", "import", "recurring", "auto", "bank_sync", "template"}
        if source not in valid_sources:
            raise ValidationError(f"source no valido: {source}. Soportado: {', '.join(sorted(valid_sources))}")

        if amount <= 0:
            raise ValidationError("amount debe ser mayor que 0")

        if income_source_id:
            source_model = await self._income_repo.get_source_by_id(income_source_id, user_id)
            if source_model is None:
                raise NotFoundError("IncomeSource")

        tx = await self._tx_repo.create(
            user_id,
            account_id=account_id,
            category_id=category_id,
            subcategory_id=subcategory_id,
            transaction_type="income",
            status=status,
            amount=Decimal(str(amount)),
            currency_code=currency_code,
            description=str(description).strip(),
            notes=notes,
            effective_date=effective_date,
            source=source,
        )

        if status == "completed":
            await self._tx_repo.update_account_balance(account_id, Decimal(str(amount)), "add")

        income = await self._income_repo.create_income(
            user_id,
            transaction_id=tx.id,
            income_type=income_type,
            income_status=income_status,
            stability=stability,
            income_source_id=income_source_id,
            employer_name=employer_name,
            employer_tax_id=employer_tax_id,
            gross_amount=Decimal(str(gross_amount)) if gross_amount is not None else None,
            tax_withheld=Decimal(str(tax_withheld)) if tax_withheld is not None else None,
            net_amount=Decimal(str(net_amount)) if net_amount is not None else None,
            frequency=frequency,
            effective_date=effective_date,
            notes=notes,
        )

        if income_source_id:
            await self._income_repo.increment_source_stats(income_source_id, Decimal(str(amount)))

        changes: dict = {"initial": {"amount": str(amount), "source": source, "income_type": income_type}}
        await self._tx_repo.create_audit_log(
            tx_id=tx.id,
            user_id=user_id,
            action="created",
            changes=changes,
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
            "income_type": income.income_type,
            "income_status": income.income_status,
            "stability": income.stability,
            "income_source_id": str(income.income_source_id) if income.income_source_id else None,
            "employer_name": income.employer_name,
            "employer_tax_id": income.employer_tax_id,
            "gross_amount": str(income.gross_amount) if income.gross_amount else None,
            "tax_withheld": str(income.tax_withheld) if income.tax_withheld else None,
            "net_amount": str(income.net_amount) if income.net_amount else None,
            "frequency": income.frequency,
            "created_at": tx.created_at.isoformat() if tx.created_at else None,
        }
