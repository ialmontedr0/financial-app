"""Use case: Create a new transaction with balance update and audit."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.transaction_repository import TransactionRepository

if TYPE_CHECKING:
    import uuid
    from datetime import date

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class CreateTransactionUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = TransactionRepository(session)

    async def execute(
        self,
        user_id: uuid.UUID,
        *,
        account_id: uuid.UUID | None = None,
        transaction_type: str,
        amount: Decimal,
        currency_code: str,
        description: str,
        effective_date: date,
        category_id: uuid.UUID | None = None,
        subcategory_id: uuid.UUID | None = None,
        status: str = "completed",
        notes: str | None = None,
        source: str = "manual",
        tags: list[str] | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        adjustment_operation: str | None = None,
        credit_card_id: uuid.UUID | None = None,
        debit_card_id: uuid.UUID | None = None,
    ) -> dict:

        from app.domain.transactions.value_objects import (
            TransactionSource,
            TransactionStatus,
            TransactionType,
        )
        from app.middleware.error_handler import NotFoundError, ValidationError

        try:
            tx_type = TransactionType(transaction_type)
        except ValueError as e:
            raise ValidationError(str(e))  # noqa: B904
        try:
            tx_status = TransactionStatus(status)
        except ValueError as e:
            raise ValidationError(str(e))  # noqa: B904
        try:
            TransactionSource(source)
        except ValueError as e:
            raise ValidationError(str(e))  # noqa: B904

        if not description or not str(description).strip():
            raise ValidationError("description es requerido")

        try:
            amount_decimal = amount
            if amount_decimal <= 0:
                raise ValidationError("amount debe ser mayor a 0")
        except ValidationError:
            raise
        except Exception:
            raise ValidationError("amount invalido")  # noqa: B904

        # Resolve debit card → linked account
        if debit_card_id:
            from app.infrastructure.repositories.debit_card_repository import DebitCardRepository

            debit_card = await DebitCardRepository(self._session).get_by_id(debit_card_id, user_id)
            if debit_card is None:
                raise NotFoundError("DebitCard")
            account_id = debit_card.account_id

        if account_id:
            account = await self._repo.get_account_by_id(account_id, user_id)
            if account is None:
                raise NotFoundError("Account")

        if credit_card_id:
            from app.infrastructure.repositories.expense_repository import ExpenseRepository

            card = await ExpenseRepository(self._session).get_credit_card_by_id(
                credit_card_id, user_id
            )
            if card is None:
                raise NotFoundError("CreditCard")

        tx = await self._repo.create(
            user_id,
            account_id=account_id,
            credit_card_id=credit_card_id,
            category_id=category_id,
            subcategory_id=subcategory_id,
            transaction_type=tx_type.value,
            status=tx_status.value,
            amount=amount_decimal,
            currency_code=currency_code,
            description=str(description).strip(),
            notes=notes,
            effective_date=effective_date,
            source=source,
        )

        if tx_status.value == "completed":
            if account_id:
                if tx_type.value == "income":
                    await self._repo.update_account_balance(account_id, amount_decimal, "add")
                elif tx_type.value == "expense":
                    await self._repo.update_account_balance(account_id, amount_decimal, "subtract")
                elif tx_type.value == "adjustment":
                    operation = adjustment_operation or "subtract"
                    await self._repo.update_account_balance(account_id, amount_decimal, operation)
            if credit_card_id and tx_type.value == "expense":
                from app.infrastructure.repositories.expense_repository import ExpenseRepository

                card = await ExpenseRepository(self._session).get_credit_card_by_id(
                    credit_card_id, user_id
                )
                if card and card.available_credit is not None:
                    from decimal import Decimal as D

                    card.available_credit -= D(str(amount))
                    await self._session.flush()

        await self._repo.create_audit_log(
            tx_id=tx.id,
            user_id=user_id,
            action="created",
            changes={"initial": {"amount": str(amount_decimal), "type": tx_type.value}},
            ip_address=ip_address,
            user_agent=user_agent,
        )

        if tags:
            await self._repo.add_tags(tx.id, user_id, tags)

        await self._session.refresh(tx)
        tag_models = await self._repo.get_tags(tx.id)

        # AI classification (async, non-blocking)
        try:
            from app.ai.classifiers.ml_classifier import classifier

            # Intenta cargar modelo si no esta cargado
            if not classifier.is_trained:
                classifier.load_model(str(user_id))

            if classifier.is_trained:
                result = await classifier.predict(description)
                if result:
                    from app.infrastructure.repositories.ai_repository import AIRepository

                    ai_repo = AIRepository(self._session)

                    from decimal import Decimal as Dec

                    await ai_repo.create_prediction(
                        user_id,
                        prediction_type="classification",
                        model_version=result["model_version"],
                        confidence=Dec(str(result["confidence"])),
                        predicted_value=result["category_slug"],
                        reason=f"Auto-classified: {result['category_slug']}",
                        features_used={"features": result["features_used"]},
                        transaction_id=tx.id,
                    )
        except Exception:
            # Classification is best-effort, never block transaction creation
            logger.info("classification_skipped", reason="model_error")
            pass

        # Publish domain event (best-effort, never blocks creation)
        from app.domain.events import EventType
        from app.infrastructure.eventbus import publish_event

        await publish_event(
            event_type=EventType.TRANSACTION_CREATED,
            aggregate_id=tx.id,
            aggregate_type="transaction",
            user_id=user_id,
            data={
                "transaction_id": str(tx.id),
                "account_id": str(tx.account_id) if tx.account_id else None,
                "category_id": str(tx.category_id) if tx.category_id else None,
                "amount": str(tx.amount),
                "currency_code": tx.currency_code,
                "transaction_type": tx.transaction_type,
                "effective_date": tx.effective_date.isoformat() if tx.effective_date else None,
            },
        )

        # Emit notification synchronously (never blocks creation)
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
            "id": str(tx.id),
            "account_id": str(tx.account_id) if tx.account_id else None,
            "category_id": str(tx.category_id) if tx.category_id else None,
            "subcategory_id": str(tx.subcategory_id) if tx.subcategory_id else None,
            "transaction_type": tx.transaction_type,
            "status": tx.status,
            "amount": str(tx.amount),
            "currency_code": tx.currency_code,
            "description": tx.description,
            "notes": tx.notes,
            "effective_date": tx.effective_date.isoformat() if tx.effective_date else None,
            "transfer_id": str(tx.transfer_id) if tx.transfer_id else None,
            "source": tx.source,
            "tags": [t.tag_name for t in tag_models],
            "credit_card_id": str(credit_card_id) if credit_card_id else None,
            "created_at": tx.created_at.isoformat() if tx.created_at else None,
        }
