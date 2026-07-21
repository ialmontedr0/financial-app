"""Analytics Use Cases."""

from .get_cash_flow import GetCashFlowUseCase
from .get_cash_flow_by_account import GetCashFlowByAccountUseCase
from .get_category_breakdown import GetCategoryBreakdownUseCase
from .get_dashboard import GetDashboardUseCase
from .get_income_trend import GetIncomeTrendUseCase
from .get_monthly_kpis import GetMonthlyKPIsUseCase
from .get_net_worth import GetNetWorthUseCase
from .get_portfolio_kpis import GetPortfolioKPIsUseCase
from .get_spending_heatmap import GetSpendingHeatmapUseCase
from .get_spending_trend import GetSpendingTrendUseCase
from .get_top_categories import GetTopCategoriesUseCase

__all__ = [
    "GetCashFlowByAccountUseCase",
    "GetCashFlowUseCase",
    "GetCategoryBreakdownUseCase",
    "GetDashboardUseCase",
    "GetIncomeTrendUseCase",
    "GetMonthlyKPIsUseCase",
    "GetNetWorthUseCase",
    "GetPortfolioKPIsUseCase",
    "GetSpendingHeatmapUseCase",
    "GetSpendingTrendUseCase",
    "GetTopCategoriesUseCase",
]
