"""Analytics endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends

from app.api.deps import get_current_active_user, get_db
from app.application.analytics.get_cash_flow import GetCashFlowUseCase
from app.application.analytics.get_cash_flow_by_account import GetCashFlowByAccountUseCase
from app.application.analytics.get_category_breakdown import GetCategoryBreakdownUseCase
from app.application.analytics.get_dashboard import GetDashboardUseCase
from app.application.analytics.get_income_trend import GetIncomeTrendUseCase
from app.application.analytics.get_monthly_kpis import GetMonthlyKPIsUseCase
from app.application.analytics.get_net_worth import GetNetWorthUseCase
from app.application.analytics.get_portfolio_kpis import GetPortfolioKPIsUseCase
from app.application.analytics.get_spending_heatmap import GetSpendingHeatmapUseCase
from app.application.analytics.get_spending_trend import GetSpendingTrendUseCase
from app.application.analytics.get_top_categories import GetTopCategoriesUseCase

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/kpis/monthly")
async def get_monthly_kpis(
    year: int | None = None,
    month: int | None = None,
    current_user: dict = Depends(get_current_active_user),  # noqa: B008
    session=Depends(get_db),  # noqa: B008
):
    user_id = uuid.UUID(current_user["sub"])
    return await GetMonthlyKPIsUseCase(session).execute(user_id, year, month)


@router.get("/kpis/portfolio")
async def get_portfolio_kpis(
    current_user: dict = Depends(get_current_active_user),  # noqa: B008
    session=Depends(get_db),  # noqa: B008
):
    user_id = uuid.UUID(current_user["sub"])
    return await GetPortfolioKPIsUseCase(session).execute(user_id)


@router.get("/trends/spending")
async def get_spending_trend(
    start_date: str | None = None,
    end_date: str | None = None,
    period: str = "monthly",
    current_user: dict = Depends(get_current_active_user),  # noqa: B008
    session=Depends(get_db),  # noqa: B008
):
    user_id = uuid.UUID(current_user["sub"])
    return await GetSpendingTrendUseCase(session).execute(user_id, start_date, end_date, period)


@router.get("/trends/income")
async def get_income_trend(
    start_date: str | None = None,
    end_date: str | None = None,
    period: str = "monthly",
    current_user: dict = Depends(get_current_active_user),  # noqa: B008
    session=Depends(get_db),  # noqa: B008
):
    user_id = uuid.UUID(current_user["sub"])
    return await GetIncomeTrendUseCase(session).execute(user_id, start_date, end_date, period)


@router.get("/categories/breakdown")
async def get_category_breakdown(
    start_date: str | None = None,
    end_date: str | None = None,
    transaction_type: str = "expense",
    current_user: dict = Depends(get_current_active_user),  # noqa: B008
    session=Depends(get_db),  # noqa: B008
):
    user_id = uuid.UUID(current_user["sub"])
    return await GetCategoryBreakdownUseCase(session).execute(
        user_id, start_date, end_date, transaction_type
    )


@router.get("/categories/top")
async def get_top_categories(
    start_date: str | None = None,
    end_date: str | None = None,
    limit: int = 5,
    transaction_type: str = "expense",
    current_user: dict = Depends(get_current_active_user),  # noqa: B008
    session=Depends(get_db),  # noqa: B008
):
    user_id = uuid.UUID(current_user["sub"])
    return await GetTopCategoriesUseCase(session).execute(
        user_id, start_date, end_date, limit, transaction_type
    )


@router.get("/cash-flow")
async def get_cash_flow(
    start_date: str | None = None,
    end_date: str | None = None,
    current_user: dict = Depends(get_current_active_user),  # noqa: B008
    session=Depends(get_db),  # noqa: B008
):
    user_id = uuid.UUID(current_user["sub"])
    return await GetCashFlowUseCase(session).execute(user_id, start_date, end_date)


@router.get("/cash-flow/by-account")
async def get_cash_flow_by_account(
    start_date: str | None = None,
    end_date: str | None = None,
    current_user: dict = Depends(get_current_active_user),  # noqa: B008
    session=Depends(get_db),  # noqa: B008
):
    user_id = uuid.UUID(current_user["sub"])
    return await GetCashFlowByAccountUseCase(session).execute(user_id, start_date, end_date)


@router.get("/net-worth")
async def get_net_worth(
    current_user: dict = Depends(get_current_active_user),  # noqa: B008
    session=Depends(get_db),  # noqa: B008
):
    user_id = uuid.UUID(current_user["sub"])
    return await GetNetWorthUseCase(session).execute(user_id)


@router.get("/heatmaps/spending")
async def get_spending_heatmap(
    start_date: str | None = None,
    end_date: str | None = None,
    granularity: str = "day_of_week_month",
    current_user: dict = Depends(get_current_active_user),  # noqa: B008
    session=Depends(get_db),  # noqa: B008
):
    user_id = uuid.UUID(current_user["sub"])
    return await GetSpendingHeatmapUseCase(session).execute(
        user_id, start_date, end_date, granularity
    )


@router.get("/dashboard")
async def get_dashboard(
    current_user: dict = Depends(get_current_active_user),  # noqa: B008
    session=Depends(get_db),  # noqa: B008
):
    user_id = uuid.UUID(current_user["sub"])
    return await GetDashboardUseCase(session).execute(user_id)
