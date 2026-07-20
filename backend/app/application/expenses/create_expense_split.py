"""Use case: Create a split expense (one parent + N children)."""

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


class CreateExpenseSplitUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._tx_repo = TransactionRepository(session)
        self._expense_repo = ExpenseRepository(session)

    async def execute(
        self,
        user_id: uuid.UUID,
        *,
        account_id: uuid.UUID,
        total_amount: float,
        currency_code: str,
        description: str,
        effective_date: date,
        splits: list[dict],  # [{"amount": 1000, "description": "Parte Juan", "account_id": "..."}]
        notes: str | None = None,
        tags: list[str] | None = None,
    ) -> dict:
        import uuid as uuid_mod
        from decimal import Decimal

        from app.middleware.error_handler import ValidationError

        if not splits:
            raise ValidationError("Al menos un split es requerido")

        split_total = sum(Decimal(str(s["amount"])) for s in splits)
        if split_total != Decimal(str(total_amount)):
            raise ValidationError(
                f"La suma de splits ({split_total}) no coincide con el total ({total_amount})"
            )

        transfer_id = uuid_mod.uuid4()

        # Create parent expense
        parent = await self._tx_repo.create(
            user_id,
            account_id=account_id,
            transaction_type="expense",
            status="completed",
            amount=Decimal(str(total_amount)),
            currency_code=currency_code,
            description=str(description).strip(),
            notes=notes,
            effective_date=effective_date,
            source="manual",
            transfer_id=transfer_id,
        )

        # Create split children
        children = []
        for split in splits:
            child_account_id = uuid_mod.UUID(split.get("account_id", str(account_id)))
            child = await self._tx_repo.create(
                user_id,
                account_id=child_account_id,
                transaction_type="expense",
                status="completed",
                amount=Decimal(str(split["amount"])),
                currency_code=currency_code,
                description=split.get("description", f"Split de {description}"),
                effective_date=effective_date,
                source="manual",
                transfer_id=transfer_id,
            )
            await self._tx_repo.update_account_balance(
                child_account_id, Decimal(str(split["amount"])), "subtract"
            )
            children.append(child)

        # Tags on parent
        if tags:
            await self._tx_repo.add_tags(parent.id, user_id, tags)

        # Audit
        await self._tx_repo.create_audit_log(
            tx_id=parent.id,
            user_id=user_id,
            action="created",
            changes={"split": {"total": str(total_amount), "child_count": len(children)}},
        )

        return {
            "id": str(parent.id),
            "transfer_id": str(transfer_id),
            "total_amount": str(total_amount),
            "split_count": len(children),
            "children": [
                {"id": str(c.id), "amount": str(c.amount), "description": c.description}
                for c in children
            ],
            "created_at": parent.created_at.isoformat() if parent.created_at else None,
        }
