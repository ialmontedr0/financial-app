"""Automation management endpoints."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_db

router = APIRouter(prefix="/automations", tags=["Automations"])


@router.get("", status_code=200)
async def list_rules(
    is_active: bool | None = None,
    trigger_type: str | None = None,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    from app.application.automations.list_rules import ListAutomationRulesUseCase

    user_id = uuid.UUID(current_user["sub"])
    return await ListAutomationRulesUseCase(db).execute(
        user_id, is_active=is_active, trigger_type=trigger_type
    )


@router.post("", status_code=201)
async def create_rule(
    body: dict[str, Any],
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    from app.application.automations.create_rule import CreateAutomationRuleUseCase

    user_id = uuid.UUID(current_user["sub"])
    return await CreateAutomationRuleUseCase(db).execute(user_id, **body)


@router.get("/templates")
async def get_templates(
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    from app.application.automations.get_templates import GetTemplatesUseCase

    user_id = uuid.UUID(current_user["sub"])
    return await GetTemplatesUseCase(db).execute(user_id)


@router.get("/summary")
async def get_summary(
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    from app.application.automations.get_summary import GetAutomationSummaryUseCase

    user_id = uuid.UUID(current_user["sub"])
    return await GetAutomationSummaryUseCase(db).execute(user_id)


@router.get("/execution-log")
async def get_execution_logs(
    rule_id: uuid.UUID | None = None,
    limit: int = 50,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    from app.application.automations.get_execution_logs import GetExecutionLogsUseCase

    user_id = uuid.UUID(current_user["sub"])
    return await GetExecutionLogsUseCase(db).execute(
        user_id, rule_id=rule_id, limit=limit
    )


@router.get("/execution-log/{log_id}")
async def get_execution_log(
    log_id: uuid.UUID,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    from app.infrastructure.repositories.automation_repository import (
        AutomationRepository,
    )
    from app.middleware.error_handler import NotFoundError

    user_id = uuid.UUID(current_user["sub"])
    repo = AutomationRepository(db)
    log = await repo.get_execution_log(log_id, user_id)
    if log is None:
        raise NotFoundError("Execution Log")
    return {
        "id": str(log.id),
        "rule_id": str(log.rule_id),
        "status": log.status,
        "trigger_snapshot": log.trigger_snapshot,
        "action_result": log.action_result,
        "error_message": log.error_message,
        "amount_involved": (
            float(log.amount_involved) if log.amount_involved else None
        ),
        "is_dry_run": log.is_dry_run,
        "executed_at": log.executed_at.isoformat() if log.executed_at else None,
    }


@router.get("/{rule_id}")
async def get_rule(
    rule_id: uuid.UUID,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    from app.application.automations.get_rule import GetAutomationRuleUseCase

    user_id = uuid.UUID(current_user["sub"])
    return await GetAutomationRuleUseCase(db).execute(user_id, rule_id)


@router.put("/{rule_id}")
async def update_rule(
    rule_id: uuid.UUID,
    body: dict[str, Any],
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    from app.application.automations.update_rule import UpdateAutomationRuleUseCase

    user_id = uuid.UUID(current_user["sub"])
    return await UpdateAutomationRuleUseCase(db).execute(user_id, rule_id, **body)


@router.delete("/{rule_id}")
async def delete_rule(
    rule_id: uuid.UUID,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    from app.application.automations.delete_rule import DeleteAutomationRuleUseCase

    user_id = uuid.UUID(current_user["sub"])
    return await DeleteAutomationRuleUseCase(db).execute(user_id, rule_id)


@router.post("/{rule_id}/toggle")
async def toggle_rule(
    rule_id: uuid.UUID,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    from app.application.automations.toggle_rule import ToggleAutomationRuleUseCase

    user_id = uuid.UUID(current_user["sub"])
    return await ToggleAutomationRuleUseCase(db).execute(user_id, rule_id)


@router.post("/{rule_id}/execute")
async def execute_rule(
    rule_id: uuid.UUID,
    dry_run: bool = False,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    from app.application.automations.execute_rule import ExecuteAutomationRuleUseCase

    user_id = uuid.UUID(current_user["sub"])
    return await ExecuteAutomationRuleUseCase(db).execute(
        user_id, rule_id, dry_run=dry_run
    )


@router.post("/evaluate")
async def evaluate_all(
    dry_run: bool = False,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    from app.application.automations.evaluate_all import EvaluateAllRulesUseCase

    user_id = uuid.UUID(current_user["sub"])
    return await EvaluateAllRulesUseCase(db).execute(user_id, dry_run=dry_run)


# ---- Quick Setup Endpoints ----


@router.post("/quick/savings-transfer")
async def quick_savings_transfer(
    body: dict[str, Any],
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    from app.application.automations.quick_savings_transfer import (
        QuickSavingsTransferUseCase,
    )

    user_id = uuid.UUID(current_user["sub"])
    return await QuickSavingsTransferUseCase(db).execute(
        user_id,
        source_account_id=uuid.UUID(body["source_account_id"]),
        target_account_id=uuid.UUID(body["target_account_id"]),
        amount=body["amount"],
        amount_type=body.get("amount_type", "fixed"),
        trigger_type=body.get("trigger_type", "income_received"),
        trigger_conditions=body.get("trigger_conditions"),
        name=body.get("name"),
    )


@router.post("/quick/card-payment")
async def quick_card_payment(
    body: dict[str, Any],
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    from app.application.automations.quick_card_payment import (
        QuickCardPaymentUseCase,
    )

    user_id = uuid.UUID(current_user["sub"])
    return await QuickCardPaymentUseCase(db).execute(
        user_id,
        card_id=uuid.UUID(body["card_id"]),
        payment_account_id=uuid.UUID(body["payment_account_id"]),
        payment_type=body.get("payment_type", "full"),
        days_before_due=body.get("days_before_due", 3),
        name=body.get("name"),
    )


@router.post("/quick/balance-transfer")
async def quick_balance_transfer(
    body: dict[str, Any],
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    from app.application.automations.quick_balance_transfer import (
        QuickBalanceTransferUseCase,
    )

    user_id = uuid.UUID(current_user["sub"])
    return await QuickBalanceTransferUseCase(db).execute(
        user_id,
        source_account_id=uuid.UUID(body["source_account_id"]),
        target_account_id=uuid.UUID(body["target_account_id"]),
        threshold=body["threshold"],
        direction=body.get("direction", "above"),
        percent_to_transfer=body.get("percent_to_transfer", 50.0),
        name=body.get("name"),
    )
