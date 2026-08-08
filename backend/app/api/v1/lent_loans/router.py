"""Lent loans endpoints (préstamo otorgado)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import get_current_active_user, get_db
from app.application.lent_loans.create import CreateLentLoanUseCase
from app.application.lent_loans.delete import DeleteLentLoanUseCase
from app.application.lent_loans.get import GetLentLoanUseCase
from app.application.lent_loans.get_summary import GetLentLoanSummaryUseCase
from app.application.lent_loans.list import ListLentLoansUseCase
from app.application.lent_loans.record_payment import RecordLentLoanPaymentUseCase
from app.application.lent_loans.simulate import SimulateLentLoanUseCase
from app.api.v1.lent_loans.schemas import (
    CreateLentLoanSchema,
    RecordLentLoanPaymentSchema,
    SimulateLentLoanSchema,
)
from app.middleware.error_handler import NotFoundError, ValidationError

router = APIRouter(prefix="/lent-loans", tags=["Lent Loans"])


@router.post("/simulate")
async def simulate_lent_loan(
    body: SimulateLentLoanSchema,
    current_user=Depends(get_current_active_user),  # noqa: B008
    session=Depends(get_db),  # noqa: B008
):
    try:
        return await SimulateLentLoanUseCase(session).execute(
            principal_amount=body.principal_amount,
            annual_interest_rate=body.annual_interest_rate,
            term_months=body.term_months,
            start_date=body.start_date,
        )
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=exc.message) from exc


@router.post("", status_code=201)
async def create_lent_loan(
    body: CreateLentLoanSchema,
    current_user: dict = Depends(get_current_active_user),  # noqa: B008
    session=Depends(get_db),  # noqa: B008
):
    user_id = uuid.UUID(current_user["sub"])
    try:
        return await CreateLentLoanUseCase(session).execute(
            user_id=user_id,
            borrower_name=body.borrower_name,
            principal_amount=body.principal_amount,
            annual_interest_rate=body.annual_interest_rate,
            term_months=body.term_months,
            payment_frequency=body.payment_frequency,
            currency_code=body.currency_code,
            account_id=body.account_id,
            start_date=body.start_date,
            is_collateralized=body.is_collateralized,
            notes=body.notes,
        )
    except ValidationError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.get("")
async def list_lent_loans(
    status: str | None = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    current_user: dict = Depends(get_current_active_user),  # noqa: B008
    session=Depends(get_db),  # noqa: B008
):
    user_id = uuid.UUID(current_user["sub"])
    return await ListLentLoansUseCase(session).execute(
        user_id, status=status, skip=skip, limit=limit
    )


@router.get("/summary")
async def get_lent_loan_summary(
    current_user: dict = Depends(get_current_active_user),  # noqa: B008
    session=Depends(get_db),  # noqa: B008
):
    user_id = uuid.UUID(current_user["sub"])
    return await GetLentLoanSummaryUseCase(session).execute(user_id)


@router.get("/{lent_loan_id}")
async def get_lent_loan(
    lent_loan_id: uuid.UUID,
    current_user: dict = Depends(get_current_active_user),  # noqa: B008
    session=Depends(get_db),  # noqa: B008
):
    user_id = uuid.UUID(current_user["sub"])
    try:
        return await GetLentLoanUseCase(session).execute(user_id, lent_loan_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.post("/{lent_loan_id}/payments", status_code=201)
async def record_lent_loan_payment(
    lent_loan_id: uuid.UUID,
    body: RecordLentLoanPaymentSchema,
    current_user: dict = Depends(get_current_active_user),  # noqa: B008
    session=Depends(get_db),  # noqa: B008
):
    user_id = uuid.UUID(current_user["sub"])
    try:
        return await RecordLentLoanPaymentUseCase(session).execute(
            user_id=user_id,
            lent_loan_id=lent_loan_id,
            amount=body.amount,
            received_date=body.received_date,
            payment_method=body.payment_method,
            reference_number=body.reference_number,
            notes=body.notes,
        )
    except (NotFoundError, ValidationError) as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.delete("/{lent_loan_id}")
async def delete_lent_loan(
    lent_loan_id: uuid.UUID,
    current_user: dict = Depends(get_current_active_user),  # noqa: B008
    session=Depends(get_db),  # noqa: B008
):
    user_id = uuid.UUID(current_user["sub"])
    try:
        return await DeleteLentLoanUseCase(session).execute(user_id, lent_loan_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc