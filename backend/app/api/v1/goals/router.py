"""Financial goals endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_db

router = APIRouter(prefix="/goals", tags=["Financial Goals"])


@router.post("", status_code=201)
async def create_goal(
    body: dict,
    current_user: dict = Depends(get_current_active_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> dict:
    from datetime import date as date_type
    from app.application.goals.create_goal import CreateGoalUseCase

    start_date = date_type.fromisoformat(body["start_date"]) if isinstance(body.get("start_date"), str) and body.get("start_date") else None
    target_date = date_type.fromisoformat(body["target_date"]) if isinstance(body.get("target_date"), str) and body.get("target_date") else None

    return await CreateGoalUseCase(db).execute(
        uuid.UUID(current_user["sub"]),
        name=body["name"], target_amount=float(body["target_amount"]),
        goal_type=body.get("goal_type", "savings"), start_date=start_date, target_date=target_date,
        monthly_contribution=float(body["monthly_contribution"]) if body.get("monthly_contribution") else None,
        interest_rate=float(body["interest_rate"]) if body.get("interest_rate") else None,
        compound_frequency=body.get("compound_frequency"),
        account_id=uuid.UUID(body["account_id"]) if body.get("account_id") else None,
        category_id=uuid.UUID(body["category_id"]) if body.get("category_id") else None,
        priority=body.get("priority", 1), auto_contribute=body.get("auto_contribute", False),
        description=body.get("description"), icon=body.get("icon"), color=body.get("color"), image_url=body.get("image_url"),
    )


@router.get("")
async def list_goals(
    current_user: dict = Depends(get_current_active_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
    goal_type: str | None = Query(None), status: str | None = Query(None), priority: int | None = Query(None),
) -> dict:
    from app.application.goals.list_goals import ListGoalsUseCase
    return await ListGoalsUseCase(db).execute(uuid.UUID(current_user["sub"]), goal_type=goal_type, status=status, priority=priority)


@router.get("/summary")
async def get_goal_summary(
    current_user: dict = Depends(get_current_active_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> dict:
    from app.application.goals.get_goal_summary import GetGoalSummaryUseCase
    return await GetGoalSummaryUseCase(db).execute(uuid.UUID(current_user["sub"]))


@router.get("/{goal_id}")
async def get_goal(
    goal_id: uuid.UUID,
    current_user: dict = Depends(get_current_active_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> dict:
    from app.application.goals.get_goal import GetGoalUseCase
    return await GetGoalUseCase(db).execute(uuid.UUID(current_user["sub"]), goal_id)


@router.patch("/{goal_id}")
async def update_goal(
    goal_id: uuid.UUID, body: dict,
    current_user: dict = Depends(get_current_active_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> dict:
    from app.application.goals.update_goal import UpdateGoalUseCase
    return await UpdateGoalUseCase(db).execute(uuid.UUID(current_user["sub"]), goal_id, changes=body)


@router.delete("/{goal_id}")
async def delete_goal(
    goal_id: uuid.UUID,
    current_user: dict = Depends(get_current_active_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> dict:
    from app.application.goals.delete_goal import DeleteGoalUseCase
    return await DeleteGoalUseCase(db).execute(uuid.UUID(current_user["sub"]), goal_id)


@router.post("/{goal_id}/refresh", status_code=200)
async def refresh_goal(
    goal_id: uuid.UUID,
    current_user: dict = Depends(get_current_active_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> dict:
    from app.application.goals.refresh_goal import RefreshGoalUseCase
    return await RefreshGoalUseCase(db).execute(uuid.UUID(current_user["sub"]), goal_id)


@router.post("/{goal_id}/predict", status_code=200)
async def refresh_prediction(
    goal_id: uuid.UUID,
    current_user: dict = Depends(get_current_active_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> dict:
    from app.application.goals.refresh_prediction import RefreshPredictionUseCase
    return await RefreshPredictionUseCase(db).execute(uuid.UUID(current_user["sub"]), goal_id)


@router.get("/{goal_id}/simulations")
async def list_simulations(
    goal_id: uuid.UUID,
    current_user: dict = Depends(get_current_active_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> dict:
    from app.application.goals.list_simulations import ListSimulationsUseCase
    return await ListSimulationsUseCase(db).execute(uuid.UUID(current_user["sub"]), goal_id)


@router.post("/{goal_id}/simulations", status_code=201)
async def create_simulation(
    goal_id: uuid.UUID, body: dict,
    current_user: dict = Depends(get_current_active_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> dict:
    from app.application.goals.create_simulation import CreateSimulationUseCase
    return await CreateSimulationUseCase(db).execute(
        uuid.UUID(current_user["sub"]), goal_id,
        name=body["name"], monthly_contribution=float(body["monthly_contribution"]),
        lump_sum=float(body["lump_sum"]) if body.get("lump_sum") else None,
        lump_sum_date=body.get("lump_sum_date"),
        interest_rate=float(body["interest_rate"]) if body.get("interest_rate") else None,
        increase_pct=float(body["increase_pct"]) if body.get("increase_pct") else None,
        notes=body.get("notes"),
    )


@router.delete("/{goal_id}/simulations/{simulation_id}")
async def delete_simulation(
    goal_id: uuid.UUID, simulation_id: uuid.UUID,
    current_user: dict = Depends(get_current_active_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> dict:
    from app.application.goals.delete_simulation import DeleteSimulationUseCase
    return await DeleteSimulationUseCase(db).execute(uuid.UUID(current_user["sub"]), goal_id, simulation_id)
