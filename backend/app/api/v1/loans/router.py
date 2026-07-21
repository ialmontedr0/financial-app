"""Loan endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends

from app.api.deps import get_current_active_user, get_db
from app.application.loans.calculate_early_payoff import CalculateEarlyPayoffUseCase
from app.application.loans.create_loan import CreateLoanUseCase
from app.application.loans.delete_loan import DeleteLoanUseCase
from app.application.loans.get_amortization_schedule import GetAmortizationScheduleUseCase
from app.application.loans.get_amortization_summary import GetAmortizationSummaryUseCase
from app.application.loans.get_loan import GetLoanUseCase
from app.application.loans.get_loans_summary import GetLoansSummaryUseCase
from app.application.loans.list_loan_payments import ListLoanPaymentsUseCase
from app.application.loans.list_loans import ListLoansUseCase
from app.application.loans.make_loan_payment import MakeLoanPaymentUseCase
from app.application.loans.simulate_loan import SimulateLoanUseCase
from app.application.loans.update_loan import UpdateLoanUseCase
from app.application.loans.update_loan_status import UpdateLoanStatusUseCase

router = APIRouter(prefix="/loans", tags=["Loans"])


@router.post("", status_code=201)
async def create_loan(
    body: dict,
    current_user: dict = Depends(get_current_active_user),  # noqa: B008
    session=Depends(get_db),  # noqa: B008
):
    user_id = uuid.UUID(current_user["sub"])
    return await CreateLoanUseCase(session).execute(
        user_id=user_id,
        name=body.get("name", ""),
        principal_amount=body.get("principal_amount", 0),
        annual_interest_rate=body.get("annual_interest_rate", 0),
        term_months=body.get("term_months", 0),
        loan_type=body.get("loan_type", "personal"),
        interest_type=body.get("interest_type", "fixed"),
        payment_frequency=body.get("payment_frequency", "monthly"),
        account_id=body.get("account_id"),
        lender_name=body.get("lender_name"),
        account_number=body.get("account_number"),
        disbursement_date=body.get("disbursement_date"),
        grace_period_days=body.get("grace_period_days", 0),
        early_payoff_allowed=body.get("early_payoff_allowed", True),
        early_payoff_penalty_pct=body.get("early_payoff_penalty_pct"),
        penalty_rate_monthly=body.get("penalty_rate_monthly"),
        notes=body.get("notes"),
    )


@router.get("")
async def list_loans(
    status: str | None = None,
    loan_type: str | None = None,
    current_user: dict = Depends(get_current_active_user),  # noqa: B008
    session=Depends(get_db),  # noqa: B008
):
    user_id = uuid.UUID(current_user["sub"])
    return await ListLoansUseCase(session).execute(user_id, status=status, loan_type=loan_type)


@router.get("/summary")
async def get_loans_summary(
    current_user: dict = Depends(get_current_active_user),  # noqa: B008
    session=Depends(get_db),  # noqa: B008
):
    user_id = uuid.UUID(current_user["sub"])
    return await GetLoansSummaryUseCase(session).execute(user_id)


@router.post("/simulate")
async def simulate_loan(
    body: dict,
    current_user: dict = Depends(get_current_active_user),  # noqa: B008
):
    return await SimulateLoanUseCase().execute(
        principal_amount=body.get("principal_amount", 0),
        annual_interest_rate=body.get("annual_interest_rate", 0),
        term_months=body.get("term_months", 0),
        start_date=body.get("start_date"),
        extra_monthly_payment=body.get("extra_monthly_payment", 0),
    )


@router.get("/{loan_id}")
async def get_loan(
    loan_id: uuid.UUID,
    current_user: dict = Depends(get_current_active_user),  # noqa: B008
    session=Depends(get_db),  # noqa: B008
):
    user_id = uuid.UUID(current_user["sub"])
    return await GetLoanUseCase(session).execute(user_id, loan_id)


@router.patch("/{loan_id}")
async def update_loan(
    loan_id: uuid.UUID,
    body: dict,
    current_user: dict = Depends(get_current_active_user),  # noqa: B008
    session=Depends(get_db),  # noqa: B008
):
    user_id = uuid.UUID(current_user["sub"])
    return await UpdateLoanUseCase(session).execute(user_id, loan_id, body)


@router.delete("/{loan_id}")
async def delete_loan(
    loan_id: uuid.UUID,
    current_user: dict = Depends(get_current_active_user),  # noqa: B008
    session=Depends(get_db),  # noqa: B008
):
    user_id = uuid.UUID(current_user["sub"])
    return await DeleteLoanUseCase(session).execute(user_id, loan_id)


@router.patch("/{loan_id}/status")
async def update_loan_status(
    loan_id: uuid.UUID,
    body: dict,
    current_user: dict = Depends(get_current_active_user),  # noqa: B008
    session=Depends(get_db),  # noqa: B008
):
    user_id = uuid.UUID(current_user["sub"])
    return await UpdateLoanStatusUseCase(session).execute(user_id, loan_id, body.get("status", ""))


@router.get("/{loan_id}/amortization")
async def get_amortization_schedule(
    loan_id: uuid.UUID,
    paid_only: bool = False,
    current_user: dict = Depends(get_current_active_user),  # noqa: B008
    session=Depends(get_db),  # noqa: B008
):
    user_id = uuid.UUID(current_user["sub"])
    return await GetAmortizationScheduleUseCase(session).execute(
        user_id, loan_id, paid_only=paid_only
    )


@router.get("/{loan_id}/amortization/summary")
async def get_amortization_summary(
    loan_id: uuid.UUID,
    current_user: dict = Depends(get_current_active_user),  # noqa: B008
    session=Depends(get_db),  # noqa: B008
):
    user_id = uuid.UUID(current_user["sub"])
    return await GetAmortizationSummaryUseCase(session).execute(user_id, loan_id)


@router.post("/{loan_id}/payments", status_code=201)
async def make_loan_payment(
    loan_id: uuid.UUID,
    body: dict,
    current_user: dict = Depends(get_current_active_user),  # noqa: B008
    session=Depends(get_db),  # noqa: B008
):
    user_id = uuid.UUID(current_user["sub"])
    return await MakeLoanPaymentUseCase(session).execute(
        user_id=user_id,
        loan_id=loan_id,
        amount=body.get("amount", 0),
        payment_date=body.get("payment_date"),
        payment_method=body.get("payment_method", "bank_transfer"),
        reference_number=body.get("reference_number"),
        is_extra_payment=body.get("is_extra_payment", False),
        notes=body.get("notes"),
    )


@router.get("/{loan_id}/payments")
async def list_loan_payments(
    loan_id: uuid.UUID,
    limit: int = 50,
    offset: int = 0,
    current_user: dict = Depends(get_current_active_user),  # noqa: B008
    session=Depends(get_db),  # noqa: B008
):
    user_id = uuid.UUID(current_user["sub"])
    return await ListLoanPaymentsUseCase(session).execute(
        user_id, loan_id, limit=limit, offset=offset
    )


@router.get("/{loan_id}/early-payoff")
async def calculate_early_payoff(
    loan_id: uuid.UUID,
    payoff_date: str | None = None,
    current_user: dict = Depends(get_current_active_user),  # noqa: B008
    session=Depends(get_db),  # noqa: B008
):
    user_id = uuid.UUID(current_user["sub"])
    return await CalculateEarlyPayoffUseCase(session).execute(
        user_id, loan_id, payoff_date=payoff_date
    )
