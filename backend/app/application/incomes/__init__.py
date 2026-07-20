"""Incomes application use cases."""

from app.application.incomes.create_income import CreateIncomeUseCase
from app.application.incomes.get_income import GetIncomeUseCase
from app.application.incomes.update_income import UpdateIncomeUseCase
from app.application.incomes.delete_income import DeleteIncomeUseCase
from app.application.incomes.list_incomes import ListIncomesUseCase
from app.application.incomes.create_income_bulk import CreateIncomeBulkUseCase
from app.application.incomes.create_from_source import CreateFromSourceUseCase
from app.application.incomes.create_source import CreateSourceUseCase
from app.application.incomes.list_sources import ListSourcesUseCase
from app.application.incomes.update_source import UpdateSourceUseCase
from app.application.incomes.delete_source import DeleteSourceUseCase
from app.application.incomes.create_schedule import CreateScheduleUseCase
from app.application.incomes.list_schedule import ListScheduleUseCase
from app.application.incomes.update_schedule import UpdateScheduleUseCase
from app.application.incomes.delete_schedule import DeleteScheduleUseCase
from app.application.incomes.receive_scheduled import ReceiveScheduledUseCase
from app.application.incomes.auto_detect_recurring import AutoDetectRecurringUseCase
from app.application.incomes.detect_irregular import DetectIrregularUseCase
from app.application.incomes.import_bank_csv import ImportBankCSVUseCase
from app.application.incomes.list_recurring_incomes import ListRecurringIncomesUseCase
from app.application.incomes.process_recurring_income import ProcessRecurringIncomeUseCase
from app.application.incomes.get_income_summary import GetIncomeSummaryUseCase
from app.application.incomes.get_income_trends import GetIncomeTrendsUseCase
from app.application.incomes.get_income_forecast import GetIncomeForecastUseCase
from app.application.incomes.get_income_by_source import GetIncomeBySourceUseCase
from app.application.incomes.get_income_by_category import GetIncomeByCategoryUseCase
from app.application.incomes.get_monthly_breakdown import GetMonthlyBreakdownUseCase
from app.application.incomes.create_quick_income import CreateQuickIncomeUseCase
from app.application.incomes.batch_update_status import BatchUpdateStatusUseCase

__all__ = [
    "CreateIncomeUseCase", "GetIncomeUseCase", "UpdateIncomeUseCase",
    "DeleteIncomeUseCase", "ListIncomesUseCase", "CreateIncomeBulkUseCase",
    "CreateFromSourceUseCase", "CreateSourceUseCase", "ListSourcesUseCase",
    "UpdateSourceUseCase", "DeleteSourceUseCase", "CreateScheduleUseCase",
    "ListScheduleUseCase", "UpdateScheduleUseCase", "DeleteScheduleUseCase",
    "ReceiveScheduledUseCase", "AutoDetectRecurringUseCase", "DetectIrregularUseCase",
    "ImportBankCSVUseCase", "ListRecurringIncomesUseCase", "ProcessRecurringIncomeUseCase",
    "GetIncomeSummaryUseCase", "GetIncomeTrendsUseCase", "GetIncomeForecastUseCase",
    "GetIncomeBySourceUseCase", "GetIncomeByCategoryUseCase", "GetMonthlyBreakdownUseCase",
    "CreateQuickIncomeUseCase", "BatchUpdateStatusUseCase",
]
