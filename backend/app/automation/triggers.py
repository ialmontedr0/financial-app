"""Trigger evaluators - check if automation conditions are met."""

from __future__ import annotations

import uuid
from datetime import date, timedelta

import structlog
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.models.automation_rule import AutomationRuleModel
from app.infrastructure.models.budget import BudgetModel
from app.infrastructure.models.credit_card_bill import CreditCardBillModel
from app.infrastructure.models.financial_account import FinancialAccountModel
from app.infrastructure.models.financial_goal import FinancialGoalModel
from app.infrastructure.models.transaction import TransactionModel

logger = structlog.get_logger()


class TriggerEvaluator:
    """Evaluates trigger conditions for automation rules."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def evaluate(self, rule: AutomationRuleModel) -> bool:
        """Evaluate if a rule's trigger condition is met."""
        evaluator = getattr(self, f"_eval_{rule.trigger_type}", None)
        if evaluator is None:
            logger.warning("unknown_trigger_type", trigger=rule.trigger_type)
            return False

        try:
            return await evaluator(rule)
        except Exception as e:
            logger.error(
                "trigger_evaluation_error",
                rule_id=str(rule.id),
                trigger=rule.trigger_type,
                error=str(e),
            )
            return False

    async def _eval_income_received(self, rule: AutomationRuleModel) -> bool:
        """Check if an income transaction was recently created."""
        conditions = rule.trigger_conditions or {}
        min_amount = conditions.get("min_amount", 0)
        category_id = conditions.get("category_id")

        yesterday = date.today() - timedelta(days=1)
        stmt = select(func.coalesce(func.sum(TransactionModel.amount), 0)).where(
            and_(
                TransactionModel.user_id == rule.user_id,
                TransactionModel.transaction_type == "income",
                TransactionModel.status == "completed",
                TransactionModel.deleted_at.is_(None),
                TransactionModel.effective_date >= yesterday,
            )
        )
        if category_id:
            stmt = stmt.where(TransactionModel.category_id == uuid.UUID(category_id))

        result = await self._session.execute(stmt)
        total = float(result.scalar() or 0)

        return total >= min_amount

    async def _eval_balance_threshold(self, rule: AutomationRuleModel) -> bool:
        """Check if an account balance crossed a threshold."""
        conditions = rule.trigger_conditions or {}
        account_id = conditions.get("account_id")
        threshold = float(conditions.get("threshold", 0))
        direction = conditions.get("direction", "above")

        if not account_id:
            return False

        stmt = select(FinancialAccountModel).where(
            FinancialAccountModel.id == uuid.UUID(account_id)
        )
        result = await self._session.execute(stmt)
        account = result.scalar_one_or_none()

        if account is None:
            return False

        balance = float(account.balance)
        if direction == "above":
            return balance >= threshold
        else:
            return balance <= threshold

    async def _eval_date_scheduled(self, rule: AutomationRuleModel) -> bool:
        """Check if today matches the scheduled date."""
        conditions = rule.trigger_conditions or {}
        day_of_month = conditions.get("day_of_month")
        months = conditions.get("months", list(range(1, 13)))

        if day_of_month is None:
            return False

        today = date.today()
        return today.day == day_of_month and today.month in months

    async def _eval_bill_due_soon(self, rule: AutomationRuleModel) -> bool:
        """Check if a credit card bill is due within N days."""
        conditions = rule.trigger_conditions or {}
        card_id = conditions.get("card_id")
        days_before = conditions.get("days_before_due", 3)

        if not card_id:
            return False

        today = date.today()
        deadline = today + timedelta(days=days_before)

        stmt = select(CreditCardBillModel).where(
            and_(
                CreditCardBillModel.credit_card_id == uuid.UUID(card_id),
                CreditCardBillModel.payment_status == "pending",
                CreditCardBillModel.due_date <= deadline,
                CreditCardBillModel.due_date >= today,
                CreditCardBillModel.deleted_at.is_(None),
            )
        )
        result = await self._session.execute(stmt)
        bill = result.scalar_one_or_none()

        return bill is not None

    async def _eval_budget_exceeded(self, rule: AutomationRuleModel) -> bool:
        """Check if a budget has been exceeded."""
        conditions = rule.trigger_conditions or {}
        budget_id = conditions.get("budget_id")
        threshold_pct = conditions.get("threshold_pct", 90)

        if not budget_id:
            return False

        stmt = select(BudgetModel).where(BudgetModel.id == uuid.UUID(budget_id))
        result = await self._session.execute(stmt)
        budget = result.scalar_one_or_none()

        if budget is None or budget.amount <= 0:
            return False

        utilization = (float(budget.spent) / float(budget.amount)) * 100
        return utilization >= threshold_pct

    async def _eval_goal_completed(self, rule: AutomationRuleModel) -> bool:
        """Check if a financial goal has been completed."""
        conditions = rule.trigger_conditions or {}
        goal_id = conditions.get("goal_id")

        if not goal_id:
            return False

        stmt = select(FinancialGoalModel).where(
            FinancialGoalModel.id == uuid.UUID(goal_id)
        )
        result = await self._session.execute(stmt)
        goal = result.scalar_one_or_none()

        if goal is None:
            return False

        return goal.current_amount >= goal.target_amount
