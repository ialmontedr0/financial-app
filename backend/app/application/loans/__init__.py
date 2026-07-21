"""Loan use cases."""

from .calculate_early_payoff import CalculateEarlyPayoffUseCase
from .create_loan import CreateLoanUseCase
from .delete_loan import DeleteLoanUseCase
from .get_amortization_schedule import GetAmortizationScheduleUseCase
from .get_amortization_summary import GetAmortizationSummaryUseCase
from .get_loan import GetLoanUseCase
from .get_loans_summary import GetLoansSummaryUseCase
from .list_loan_payments import ListLoanPaymentsUseCase
from .list_loans import ListLoansUseCase
from .make_loan_payment import MakeLoanPaymentUseCase
from .simulate_loan import SimulateLoanUseCase
from .update_loan import UpdateLoanUseCase
from .update_loan_status import UpdateLoanStatusUseCase

__all__ = [
    "CalculateEarlyPayoffUseCase",
    "CreateLoanUseCase",
    "DeleteLoanUseCase",
    "GetAmortizationScheduleUseCase",
    "GetAmortizationSummaryUseCase",
    "GetLoanUseCase",
    "GetLoansSummaryUseCase",
    "ListLoanPaymentsUseCase",
    "ListLoansUseCase",
    "MakeLoanPaymentUseCase",
    "SimulateLoanUseCase",
    "UpdateLoanStatusUseCase",
    "UpdateLoanUseCase",
]
