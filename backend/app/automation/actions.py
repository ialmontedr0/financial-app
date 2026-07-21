"""Action executors - perform the automation action."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any

import structlog
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.models.automation_rule import AutomationRuleModel
from app.infrastructure.models.credit_card_bill import CreditCardBillModel
from app.infrastructure.models.financial_account import FinancialAccountModel
from app.infrastructure.models.transaction import TransactionModel

logger = structlog.get_logger()


class ActionExecutor:
    """Executes automation actions."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(
        self, rule: AutomationRuleModel, dry_run: bool = False
    ) -> dict[str, Any]:
        """Execute the action defined in a rule."""
        executor = getattr(self, f"_exec_{rule.action_type}", None)
        if executor is None:
            raise ValueError(f"Unknown action type: {rule.action_type}")

        return await executor(rule, dry_run)

    async def _exec_transfer(
        self, rule: AutomationRuleModel, dry_run: bool
    ) -> dict[str, Any]:
        """Transfer money between accounts."""
        params = rule.action_params or {}
        source_id = uuid.UUID(params["source_account_id"])
        target_id = uuid.UUID(params["target_account_id"])
        amount_value = float(params["amount"])
        amount_type = params.get("amount_type", "fixed")

        source = await self._get_account(source_id)
        if source is None:
            raise ValueError("Source account not found")

        if rule.min_balance_required:
            if float(source.balance) < float(rule.min_balance_required):
                raise ValueError(
                    f"Insufficient balance: {source.balance} < {rule.min_balance_required}"
                )

        if amount_type == "fixed":
            actual_amount = Decimal(str(amount_value))
        elif amount_type == "percent_of_balance":
            actual_amount = source.balance * Decimal(str(amount_value / 100))
        elif amount_type == "percent_of_surplus":
            min_bal = Decimal(str(rule.min_balance_required or 0))
            surplus = max(Decimal("0"), source.balance - min_bal)
            actual_amount = surplus * Decimal(str(amount_value / 100))
        else:
            actual_amount = Decimal(str(amount_value))

        if actual_amount <= 0:
            raise ValueError("Calculated amount is zero or negative")

        if float(actual_amount) > float(source.balance):
            raise ValueError(
                f"Insufficient funds: need {actual_amount}, have {source.balance}"
            )

        if dry_run:
            return {
                "action": "transfer",
                "source_account_id": str(source_id),
                "target_account_id": str(target_id),
                "amount": float(actual_amount),
                "source_balance_before": float(source.balance),
                "dry_run": True,
            }

        source.balance -= actual_amount
        target = await self._get_account(target_id)
        if target is None:
            raise ValueError("Target account not found")
        target.balance += actual_amount

        transfer_id = uuid.uuid4()

        expense_tx = TransactionModel(
            user_id=rule.user_id,
            account_id=source_id,
            transaction_type="transfer",
            status="completed",
            amount=actual_amount,
            currency_code=source.currency_code,
            description=f"Transferencia automatica: {rule.name}",
            effective_date=date.today(),
            transfer_id=transfer_id,
            source="automation",
        )
        income_tx = TransactionModel(
            user_id=rule.user_id,
            account_id=target_id,
            transaction_type="transfer",
            status="completed",
            amount=actual_amount,
            currency_code=target.currency_code,
            description=f"Transferencia automatica: {rule.name}",
            effective_date=date.today(),
            transfer_id=transfer_id,
            source="automation",
        )

        self._session.add(expense_tx)
        self._session.add(income_tx)
        await self._session.flush()

        return {
            "action": "transfer",
            "source_account_id": str(source_id),
            "target_account_id": str(target_id),
            "amount": float(actual_amount),
            "source_balance_after": float(source.balance),
            "target_balance_after": float(target.balance),
            "transfer_id": str(transfer_id),
            "transactions_created": 2,
        }

    async def _exec_pay_credit_card(
        self, rule: AutomationRuleModel, dry_run: bool
    ) -> dict[str, Any]:
        """Pay a credit card bill."""
        params = rule.action_params or {}
        card_id = uuid.UUID(params["card_id"])
        payment_account_id = uuid.UUID(params["payment_account_id"])
        payment_type = params.get("payment_type", "full")
        custom_amount = params.get("custom_amount")

        stmt = select(CreditCardBillModel).where(
            and_(
                CreditCardBillModel.credit_card_id == card_id,
                CreditCardBillModel.payment_status == "pending",
                CreditCardBillModel.deleted_at.is_(None),
            )
        ).order_by(CreditCardBillModel.due_date)
        result = await self._session.execute(stmt)
        bill = result.scalar_one_or_none()

        if bill is None:
            raise ValueError("No pending bill found for this card")

        if payment_type == "minimum" and bill.minimum_payment:
            payment_amount = bill.minimum_payment
        elif payment_type == "full":
            payment_amount = bill.total_amount - bill.amount_paid
        elif payment_type == "custom" and custom_amount:
            payment_amount = Decimal(str(custom_amount))
        else:
            payment_amount = bill.total_amount - bill.amount_paid

        if payment_amount <= 0:
            raise ValueError("Payment amount is zero or negative")

        payment_account = await self._get_account(payment_account_id)
        if payment_account is None:
            raise ValueError("Payment account not found")

        if float(payment_account.balance) < float(payment_amount):
            raise ValueError(
                f"Insufficient funds: need {payment_amount}, "
                f"have {payment_account.balance}"
            )

        if dry_run:
            return {
                "action": "pay_credit_card",
                "card_id": str(card_id),
                "bill_id": str(bill.id),
                "payment_account_id": str(payment_account_id),
                "amount": float(payment_amount),
                "payment_type": payment_type,
                "dry_run": True,
            }

        payment_account.balance -= payment_amount
        bill.amount_paid += payment_amount

        if bill.amount_paid >= bill.total_amount:
            bill.payment_status = "paid"
            bill.paid_at = datetime.utcnow()

        tx = TransactionModel(
            user_id=rule.user_id,
            account_id=payment_account_id,
            credit_card_id=card_id,
            transaction_type="expense",
            status="completed",
            amount=payment_amount,
            currency_code=payment_account.currency_code,
            description=f"Pago automatico tarjeta",
            effective_date=date.today(),
            source="automation",
        )
        self._session.add(tx)
        await self._session.flush()

        return {
            "action": "pay_credit_card",
            "card_id": str(card_id),
            "bill_id": str(bill.id),
            "payment_account_id": str(payment_account_id),
            "amount": float(payment_amount),
            "payment_type": payment_type,
            "bill_status": bill.payment_status,
            "transaction_id": str(tx.id),
        }

    async def _exec_create_transaction(
        self, rule: AutomationRuleModel, dry_run: bool
    ) -> dict[str, Any]:
        """Create a transaction automatically."""
        params = rule.action_params or {}
        account_id = uuid.UUID(params["account_id"])
        category_id = (
            uuid.UUID(params["category_id"]) if params.get("category_id") else None
        )
        amount = Decimal(str(params["amount"]))
        description = params.get("description", "Transaccion automatica")
        transaction_type = params.get("transaction_type", "expense")

        if dry_run:
            return {
                "action": "create_transaction",
                "account_id": str(account_id),
                "amount": float(amount),
                "type": transaction_type,
                "description": description,
                "dry_run": True,
            }

        tx = TransactionModel(
            user_id=rule.user_id,
            account_id=account_id,
            category_id=category_id,
            transaction_type=transaction_type,
            status="completed",
            amount=amount,
            currency_code="DOP",
            description=description,
            effective_date=date.today(),
            source="automation",
        )
        self._session.add(tx)
        await self._session.flush()

        return {
            "action": "create_transaction",
            "transaction_id": str(tx.id),
            "account_id": str(account_id),
            "amount": float(amount),
            "type": transaction_type,
            "description": description,
        }

    async def _exec_notify(
        self, rule: AutomationRuleModel, dry_run: bool
    ) -> dict[str, Any]:
        """Send notification (placeholder for Phase 18)."""
        params = rule.action_params or {}
        message = params.get("message", "Notificacion de automatizacion")

        return {
            "action": "notify",
            "message": message,
            "channel": params.get("channel", "in_app"),
            "status": "queued",
            "note": "Full notification system will be implemented in Phase 18",
        }

    async def _exec_adjust_budget(
        self, rule: AutomationRuleModel, dry_run: bool
    ) -> dict[str, Any]:
        """Auto-adjust budget amount."""
        from app.infrastructure.models.budget import BudgetModel

        params = rule.action_params or {}
        budget_id = uuid.UUID(params["budget_id"])
        adjustment_type = params.get("adjustment_type", "set")
        target_amount = Decimal(str(params.get("target_amount", 0)))

        stmt = select(BudgetModel).where(BudgetModel.id == budget_id)
        result = await self._session.execute(stmt)
        budget = result.scalar_one_or_none()

        if budget is None:
            raise ValueError("Budget not found")

        old_amount = budget.amount

        if dry_run:
            return {
                "action": "adjust_budget",
                "budget_id": str(budget_id),
                "old_amount": float(old_amount),
                "new_amount": float(target_amount),
                "adjustment_type": adjustment_type,
                "dry_run": True,
            }

        if adjustment_type == "set":
            budget.amount = target_amount
        elif adjustment_type == "increase":
            budget.amount += target_amount
        elif adjustment_type == "decrease":
            budget.amount = max(Decimal("0"), budget.amount - target_amount)
        elif adjustment_type == "percentage":
            budget.amount = budget.amount * (target_amount / 100)

        await self._session.flush()

        return {
            "action": "adjust_budget",
            "budget_id": str(budget_id),
            "old_amount": float(old_amount),
            "new_amount": float(budget.amount),
            "adjustment_type": adjustment_type,
        }

    async def _get_account(
        self, account_id: uuid.UUID
    ) -> FinancialAccountModel | None:
        """Get a financial account by ID."""
        stmt = select(FinancialAccountModel).where(
            FinancialAccountModel.id == account_id
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
