"""Automation engine - evaluates triggers and executes actions."""

from __future__ import annotations

import uuid
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.models.automation_rule import AutomationRuleModel
from app.infrastructure.repositories.automation_repository import AutomationRepository

logger = structlog.get_logger()


class AutomationEngine:
    """Core engine that evaluates rules and executes actions."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = AutomationRepository(session)

    async def evaluate_all(
        self, user_id: uuid.UUID, dry_run: bool = False
    ) -> dict[str, Any]:
        """Evaluate all active rules for a user.

        Returns summary of executions.
        """
        rules = await self._repo.get_all_active_rules(user_id)
        results: list[dict[str, Any]] = []

        for rule in rules:
            result = await self._evaluate_rule(rule, dry_run=dry_run)
            results.append(result)

        executed = sum(1 for r in results if r["status"] == "executed")
        skipped = sum(1 for r in results if r["status"] == "skipped")
        failed = sum(1 for r in results if r["status"] == "failed")

        return {
            "total_rules": len(rules),
            "executed": executed,
            "skipped": skipped,
            "failed": failed,
            "results": results,
        }

    async def execute_rule(
        self,
        rule_id: uuid.UUID,
        user_id: uuid.UUID,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """Manually execute a specific rule."""
        rule = await self._repo.get_rule(rule_id, user_id)
        if rule is None:
            return {"status": "error", "message": "Rule not found"}
        if not rule.is_active:
            return {"status": "error", "message": "Rule is inactive"}

        return await self._evaluate_rule(rule, dry_run=dry_run)

    async def _evaluate_rule(
        self, rule: AutomationRuleModel, dry_run: bool = False
    ) -> dict[str, Any]:
        """Evaluate a single rule: check trigger, execute action."""
        # Check monthly limit
        if rule.max_executions_per_month:
            allowed = await self._repo.check_monthly_limit(
                rule.id, rule.max_executions_per_month
            )
            if not allowed:
                return {
                    "rule_id": str(rule.id),
                    "rule_name": rule.name,
                    "status": "skipped",
                    "reason": "monthly_limit_reached",
                }

        # Evaluate trigger
        from app.automation.triggers import TriggerEvaluator

        evaluator = TriggerEvaluator(self._session)
        trigger_met = await evaluator.evaluate(rule)

        if not trigger_met:
            return {
                "rule_id": str(rule.id),
                "rule_name": rule.name,
                "status": "skipped",
                "reason": "trigger_not_met",
            }

        # Execute action
        try:
            from app.automation.actions import ActionExecutor

            executor = ActionExecutor(self._session)
            result = await executor.execute(rule, dry_run=dry_run)

            status = "dry_run" if dry_run else "success"

            # Log execution
            await self._repo.create_execution_log(
                rule_id=rule.id,
                user_id=rule.user_id,
                status=status,
                trigger_snapshot=rule.trigger_conditions,
                action_result=result,
                amount_involved=result.get("amount"),
                source_account_id=result.get("source_account_id"),
                target_account_id=result.get("target_account_id"),
                is_dry_run=dry_run,
            )

            if not dry_run:
                await self._repo.increment_execution(rule.id, "success")

            return {
                "rule_id": str(rule.id),
                "rule_name": rule.name,
                "status": "executed" if not dry_run else "dry_run",
                "result": result,
            }

        except Exception as e:
            logger.error(
                "automation_execution_failed",
                rule_id=str(rule.id),
                error=str(e),
            )
            await self._repo.create_execution_log(
                rule_id=rule.id,
                user_id=rule.user_id,
                status="failed",
                trigger_snapshot=rule.trigger_conditions,
                error_message=str(e),
            )
            await self._repo.increment_execution(rule.id, "failed")

            return {
                "rule_id": str(rule.id),
                "rule_name": rule.name,
                "status": "failed",
                "error": str(e),
            }
