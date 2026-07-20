"""Use case: Create a transfer between two accounts (two linked transactions)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.transaction_repository import TransactionRepository

if TYPE_CHECKING:
    import uuid
    from datetime import date

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class CreateTransferUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = TransactionRepository(session)

    async def execute(self, user_id: uuid.UUID, *, source_account_id: uuid.UUID,
        destination_account_id: uuid.UUID, amount: float, currency_code: str,
        description: str, effective_date: date, notes: str | None = None,
        tags: list[str] | None = None, ip_address: str | None = None, user_agent: str | None = None,
    ) -> dict:
        import uuid as uuid_mod
        from decimal import Decimal

        from app.middleware.error_handler import NotFoundError, ValidationError

        if source_account_id == destination_account_id:
            raise ValidationError("source y destination no pueden ser la misma cuenta")

        try:
            amount_decimal = Decimal(str(amount))
            if amount_decimal <= 0:
                raise ValidationError("amount debe ser mayor a 0")
        except ValidationError:
            raise
        except Exception:
            raise ValidationError("amount invalido")  # noqa: B904

        source_acc = await self._repo.get_account_by_id(source_account_id, user_id)
        if source_acc is None:
            raise NotFoundError("Source Account")
        dest_acc = await self._repo.get_account_by_id(destination_account_id, user_id)
        if dest_acc is None:
            raise NotFoundError("Destination Account")

        transfer_id = uuid_mod.uuid4()

        tx1 = await self._repo.create(user_id, account_id=source_account_id, transaction_type="expense",
            status="completed", amount=amount_decimal, currency_code=currency_code, description=description,
            notes=notes, effective_date=effective_date, source="manual", transfer_id=transfer_id,
        )
        tx2 = await self._repo.create(user_id, account_id=destination_account_id, transaction_type="income",
            status="completed", amount=amount_decimal, currency_code=currency_code, description=description,
            notes=notes, effective_date=effective_date, source="manual", transfer_id=transfer_id,
        )

        await self._repo.update_account_balance(source_account_id, amount_decimal, "subtract")
        await self._repo.update_account_balance(destination_account_id, amount_decimal, "add")

        for tx, role in [(tx1, "source"), (tx2, "destination")]:
            await self._repo.create_audit_log(tx_id=tx.id, user_id=user_id, action="created",
                changes={"transfer": {"pair": str(transfer_id), "role": role, "amount": str(amount_decimal)}},
                ip_address=ip_address, user_agent=user_agent,
            )

        if tags:
            await self._repo.add_tags(tx1.id, user_id, tags)
            await self._repo.add_tags(tx2.id, user_id, tags)

        return {
            "transfer_id": str(transfer_id),
            "source_transaction": {"id": str(tx1.id), "account_id": str(tx1.account_id), "amount": str(tx1.amount), "type": tx1.transaction_type},
            "destination_transaction": {"id": str(tx2.id), "account_id": str(tx2.account_id), "amount": str(tx2.amount), "type": tx2.transaction_type},
            "total_amount": str(amount_decimal), "currency_code": currency_code,
            "effective_date": effective_date.isoformat(), "created_at": tx1.created_at.isoformat() if tx1.created_at else None,
        }
