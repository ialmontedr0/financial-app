"""Budget management endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_db

router = APIRouter(prefix="/budgets", tags=["Budgets"])


# ======================================================================
# Budget CRUD
# ======================================================================


@router.post("", status_code=201)
async def create_budget(
    body: dict,
    current_user: dict = Depends(get_current_active_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> dict:
    from datetime import date as date_type

    from app.application.budgets.create_budget import CreateBudgetUseCase

    start_date = (
        date_type.fromisoformat(body["start_date"])
        if isinstance(body.get("start_date"), str) and body.get("start_date")
        else None
    )
    end_date = (
        date_type.fromisoformat(body["end_date"])
        if isinstance(body.get("end_date"), str) and body.get("end_date")
        else None
    )

    return await CreateBudgetUseCase(db).execute(
        uuid.UUID(current_user["sub"]),
        name=body["name"],
        amount=float(body["amount"]),
        budget_type=body.get("budget_type", "total"),
        period=body.get("period", "monthly"),
        start_date=start_date,
        end_date=end_date,
        category_id=uuid.UUID(body["category_id"]) if body.get("category_id") else None,
        account_id=uuid.UUID(body["account_id"]) if body.get("account_id") else None,
        alert_threshold=body.get("alert_threshold", 80),
        alert_enabled=body.get("alert_enabled", True),
        auto_adjust=body.get("auto_adjust", False),
        rollover=body.get("rollover", False),
        strategy=body.get("strategy"),
        description=body.get("description"),
        icon=body.get("icon"),
        color=body.get("color"),
    )


@router.get("")
async def list_budgets(
    current_user: dict = Depends(get_current_active_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
    budget_type: str | None = Query(None),
    is_active: bool | None = Query(None),
    period: str | None = Query(None),
) -> dict:
    from app.application.budgets.list_budgets import ListBudgetsUseCase

    return await ListBudgetsUseCase(db).execute(
        uuid.UUID(current_user["sub"]),
        budget_type=budget_type,
        is_active=is_active,
        period=period,
    )


@router.get("/summary")
async def get_budget_summary(
    current_user: dict = Depends(get_current_active_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> dict:
    from app.application.budgets.get_budget_summary import GetBudgetSummaryUseCase

    return await GetBudgetSummaryUseCase(db).execute(uuid.UUID(current_user["sub"]))


@router.get("/{budget_id}")
async def get_budget(
    budget_id: uuid.UUID,
    current_user: dict = Depends(get_current_active_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> dict:
    from app.application.budgets.get_budget import GetBudgetUseCase

    return await GetBudgetUseCase(db).execute(uuid.UUID(current_user["sub"]), budget_id)


@router.patch("/{budget_id}")
async def update_budget(
    budget_id: uuid.UUID,
    body: dict,
    current_user: dict = Depends(get_current_active_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> dict:
    from app.application.budgets.update_budget import UpdateBudgetUseCase

    return await UpdateBudgetUseCase(db).execute(
        uuid.UUID(current_user["sub"]), budget_id, changes=body
    )


@router.delete("/{budget_id}")
async def delete_budget(
    budget_id: uuid.UUID,
    current_user: dict = Depends(get_current_active_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> dict:
    from app.application.budgets.delete_budget import DeleteBudgetUseCase

    return await DeleteBudgetUseCase(db).execute(uuid.UUID(current_user["sub"]), budget_id)


@router.post("/{budget_id}/refresh", status_code=200)
async def refresh_budget(
    budget_id: uuid.UUID,
    current_user: dict = Depends(get_current_active_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> dict:
    from app.application.budgets.refresh_budget import RefreshBudgetUseCase

    return await RefreshBudgetUseCase(db).execute(uuid.UUID(current_user["sub"]), budget_id)


@router.post("/{budget_id}/auto-adjust", status_code=200)
async def auto_adjust_budget(
    budget_id: uuid.UUID,
    body: dict | None = None,
    current_user: dict = Depends(get_current_active_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> dict:
    from app.application.budgets.auto_adjust_budget import AutoAdjustBudgetUseCase

    data = body or {}
    return await AutoAdjustBudgetUseCase(db).execute(
        uuid.UUID(current_user["sub"]),
        budget_id,
        buffer_pct=float(data.get("buffer_pct", 10.0)),
        apply=data.get("apply", False),
    )


# ======================================================================
# Alerts
# ======================================================================


@router.get("/alerts/all")
async def list_alerts(
    current_user: dict = Depends(get_current_active_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
    budget_id: str | None = Query(None),
    is_read: bool | None = Query(None),
    alert_type: str | None = Query(None),
    severity: str | None = Query(None),
) -> dict:
    from app.application.budgets.list_alerts import ListAlertsUseCase

    return await ListAlertsUseCase(db).execute(
        uuid.UUID(current_user["sub"]),
        budget_id=uuid.UUID(budget_id) if budget_id else None,
        is_read=is_read,
        alert_type=alert_type,
        severity=severity,
    )


@router.post("/alerts/read", status_code=200)
async def mark_alert_read(
    body: dict,
    current_user: dict = Depends(get_current_active_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> dict:
    from app.application.budgets.mark_alert_read import MarkAlertReadUseCase

    return await MarkAlertReadUseCase(db).execute(
        uuid.UUID(current_user["sub"]),
        alert_id=uuid.UUID(body["alert_id"]) if body.get("alert_id") else None,
        mark_all=body.get("mark_all", False),
    )


@router.post("/alerts/{alert_id}/dismiss", status_code=200)
async def dismiss_alert(
    alert_id: uuid.UUID,
    current_user: dict = Depends(get_current_active_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> dict:
    from app.application.budgets.dismiss_alert import DismissAlertUseCase

    return await DismissAlertUseCase(db).execute(uuid.UUID(current_user["sub"]), alert_id)
