"""Automation repository - CRUD + queries for automation rules and execution logs."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

import structlog
from sqlalchemy import and_, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.models.automation_execution_log import AutomationExecutionLogModel
from app.infrastructure.models.automation_rule import AutomationRuleModel

logger = structlog.get_logger()


class AutomationRepository:
    """Repository for automation rules and execution logs."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ---- Rules CRUD ----

    async def create_rule(
        self,
        user_id: uuid.UUID,
        name: str,
        trigger_type: str,
        action_type: str,
        description: str | None = None,
        trigger_conditions: dict | None = None,
        action_params: dict | None = None,
        max_executions_per_month: int | None = None,
        min_balance_required: float | None = None,
    ) -> AutomationRuleModel:
        """Create a new automation rule."""
        rule = AutomationRuleModel(
            user_id=user_id,
            name=name,
            description=description,
            trigger_type=trigger_type,
            trigger_conditions=trigger_conditions,
            action_type=action_type,
            action_params=action_params,
            max_executions_per_month=max_executions_per_month,
            min_balance_required=min_balance_required,
        )
        self._session.add(rule)
        await self._session.flush()
        logger.info(
            "automation_rule_created",
            rule_id=str(rule.id),
            user_id=str(user_id),
            trigger=trigger_type,
            action=action_type,
        )
        return rule

    async def get_rule(
        self, rule_id: uuid.UUID, user_id: uuid.UUID
    ) -> AutomationRuleModel | None:
        """Get a specific rule by ID (must belong to user)."""
        stmt = select(AutomationRuleModel).where(
            and_(
                AutomationRuleModel.id == rule_id,
                AutomationRuleModel.user_id == user_id,
                AutomationRuleModel.deleted_at.is_(None),
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_rules(
        self,
        user_id: uuid.UUID,
        is_active: bool | None = None,
        trigger_type: str | None = None,
    ) -> list[AutomationRuleModel]:
        """List all rules for a user."""
        conditions = [
            AutomationRuleModel.user_id == user_id,
            AutomationRuleModel.deleted_at.is_(None),
        ]
        if is_active is not None:
            conditions.append(AutomationRuleModel.is_active == is_active)
        if trigger_type is not None:
            conditions.append(AutomationRuleModel.trigger_type == trigger_type)

        stmt = select(AutomationRuleModel).where(and_(*conditions)).order_by(
            AutomationRuleModel.created_at.desc()
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update_rule(
        self,
        rule_id: uuid.UUID,
        user_id: uuid.UUID,
        **kwargs: Any,
    ) -> AutomationRuleModel | None:
        """Update a rule."""
        rule = await self.get_rule(rule_id, user_id)
        if rule is None:
            return None
        for key, value in kwargs.items():
            if hasattr(rule, key) and value is not None:
                setattr(rule, key, value)
        await self._session.flush()
        return rule

    async def delete_rule(self, rule_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """Soft-delete a rule."""
        rule = await self.get_rule(rule_id, user_id)
        if rule is None:
            return False
        rule.deleted_at = func.now()
        await self._session.flush()
        return True

    async def toggle_rule(
        self, rule_id: uuid.UUID, user_id: uuid.UUID
    ) -> AutomationRuleModel | None:
        """Toggle active/inactive status."""
        rule = await self.get_rule(rule_id, user_id)
        if rule is None:
            return None
        rule.is_active = not rule.is_active
        await self._session.flush()
        return rule

    async def increment_execution(
        self, rule_id: uuid.UUID, status: str
    ) -> None:
        """Increment execution count and update last executed."""
        stmt = (
            update(AutomationRuleModel)
            .where(AutomationRuleModel.id == rule_id)
            .values(
                execution_count=AutomationRuleModel.execution_count + 1,
                last_executed_at=func.now(),
                last_execution_status=status,
            )
        )
        await self._session.execute(stmt)

    async def check_monthly_limit(
        self, rule_id: uuid.UUID, max_per_month: int
    ) -> bool:
        """Check if rule has exceeded monthly execution limit.
        Returns True if execution is allowed.
        """
        now = datetime.utcnow()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        stmt = select(func.count(AutomationExecutionLogModel.id)).where(
            and_(
                AutomationExecutionLogModel.rule_id == rule_id,
                AutomationExecutionLogModel.executed_at >= month_start,
                AutomationExecutionLogModel.status != "dry_run",
            )
        )
        result = await self._session.execute(stmt)
        count = result.scalar() or 0
        return count < max_per_month

    # ---- Execution Logs ----

    async def create_execution_log(
        self,
        rule_id: uuid.UUID,
        user_id: uuid.UUID,
        status: str,
        trigger_snapshot: dict | None = None,
        action_result: dict | None = None,
        error_message: str | None = None,
        amount_involved: float | None = None,
        source_account_id: uuid.UUID | None = None,
        target_account_id: uuid.UUID | None = None,
        is_dry_run: bool = False,
    ) -> AutomationExecutionLogModel:
        """Create an execution log entry."""
        log = AutomationExecutionLogModel(
            rule_id=rule_id,
            user_id=user_id,
            status=status,
            trigger_snapshot=trigger_snapshot,
            action_result=action_result,
            error_message=error_message,
            amount_involved=amount_involved,
            source_account_id=source_account_id,
            target_account_id=target_account_id,
            is_dry_run=is_dry_run,
        )
        self._session.add(log)
        await self._session.flush()
        return log

    async def list_execution_logs(
        self,
        user_id: uuid.UUID,
        rule_id: uuid.UUID | None = None,
        limit: int = 50,
    ) -> list[AutomationExecutionLogModel]:
        """List execution logs for a user."""
        conditions = [AutomationExecutionLogModel.user_id == user_id]
        if rule_id is not None:
            conditions.append(AutomationExecutionLogModel.rule_id == rule_id)

        stmt = (
            select(AutomationExecutionLogModel)
            .where(and_(*conditions))
            .order_by(AutomationExecutionLogModel.executed_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_execution_log(
        self, log_id: uuid.UUID, user_id: uuid.UUID
    ) -> AutomationExecutionLogModel | None:
        """Get a specific execution log."""
        stmt = select(AutomationExecutionLogModel).where(
            and_(
                AutomationExecutionLogModel.id == log_id,
                AutomationExecutionLogModel.user_id == user_id,
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    # ---- Queries for Trigger Evaluation ----

    async def get_rules_by_trigger(
        self, user_id: uuid.UUID, trigger_type: str
    ) -> list[AutomationRuleModel]:
        """Get all active rules for a specific trigger type."""
        stmt = select(AutomationRuleModel).where(
            and_(
                AutomationRuleModel.user_id == user_id,
                AutomationRuleModel.trigger_type == trigger_type,
                AutomationRuleModel.is_active.is_(True),
                AutomationRuleModel.deleted_at.is_(None),
            )
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_all_active_rules(
        self, user_id: uuid.UUID
    ) -> list[AutomationRuleModel]:
        """Get all active rules for a user (for batch evaluation)."""
        stmt = select(AutomationRuleModel).where(
            and_(
                AutomationRuleModel.user_id == user_id,
                AutomationRuleModel.is_active.is_(True),
                AutomationRuleModel.deleted_at.is_(None),
            )
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
