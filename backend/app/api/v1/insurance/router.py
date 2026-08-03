"""Insurance endpoints."""

from __future__ import annotations

import uuid
from datetime import date

from fastapi import APIRouter, Depends

from app.api.deps import get_current_active_user, get_db
from app.application.insurance.create_insurance import CreateInsuranceUseCase
from app.application.insurance.create_policy import CreatePolicyUseCase
from app.application.insurance.create_premium import CreatePremiumUseCase
from app.application.insurance.delete_insurance import DeleteInsuranceUseCase
from app.application.insurance.delete_policy import DeletePolicyUseCase
from app.application.insurance.delete_premium import DeletePremiumUseCase
from app.application.insurance.get_insurance import GetInsuranceUseCase
from app.application.insurance.get_insurance_dashboard import GetInsuranceDashboardUseCase
from app.application.insurance.list_insurances import ListInsurancesUseCase
from app.application.insurance.list_policies import ListPoliciesUseCase
from app.application.insurance.list_premiums import ListPremiumsUseCase
from app.application.insurance.mark_premium_paid import MarkPremiumPaidUseCase
from app.application.insurance.update_insurance import UpdateInsuranceUseCase
from app.application.insurance.update_insurance_status import UpdateInsuranceStatusUseCase

router = APIRouter(prefix="/insurance", tags=["Insurance"])


@router.post("", status_code=201)
async def create_insurance(
    body: dict,
    current_user: dict = Depends(get_current_active_user),
    session=Depends(get_db),
):
    user_id = uuid.UUID(current_user["sub"])
    return await CreateInsuranceUseCase(session).execute(
        user_id=user_id,
        name=body.get("name", ""),
        type=body.get("type", "other"),
        start_date=date.fromisoformat(body["start_date"]),
        premium_amount=body.get("premium_amount", 0),
        premium_frequency=body.get("premium_frequency", "monthly"),
        provider=body.get("provider"),
        policy_number=body.get("policy_number"),
        status=body.get("status", "active"),
        end_date=date.fromisoformat(body["end_date"]) if body.get("end_date") else None,
        coverage_amount=body.get("coverage_amount"),
        notes=body.get("notes"),
    )


@router.get("")
async def list_insurances(
    status: str | None = None,
    type: str | None = None,  # noqa: A002
    current_user: dict = Depends(get_current_active_user),
    session=Depends(get_db),
):
    user_id = uuid.UUID(current_user["sub"])
    return await ListInsurancesUseCase(session).execute(user_id, status=status, type=type)


@router.get("/dashboard")
async def get_insurance_dashboard(
    current_user: dict = Depends(get_current_active_user),
    session=Depends(get_db),
):
    user_id = uuid.UUID(current_user["sub"])
    return await GetInsuranceDashboardUseCase(session).execute(user_id)


@router.get("/{insurance_id}")
async def get_insurance(
    insurance_id: uuid.UUID,
    current_user: dict = Depends(get_current_active_user),
    session=Depends(get_db),
):
    user_id = uuid.UUID(current_user["sub"])
    return await GetInsuranceUseCase(session).execute(user_id, insurance_id)


@router.patch("/{insurance_id}")
async def update_insurance(
    insurance_id: uuid.UUID,
    body: dict,
    current_user: dict = Depends(get_current_active_user),
    session=Depends(get_db),
):
    user_id = uuid.UUID(current_user["sub"])
    return await UpdateInsuranceUseCase(session).execute(user_id, insurance_id, body)


@router.delete("/{insurance_id}")
async def delete_insurance(
    insurance_id: uuid.UUID,
    current_user: dict = Depends(get_current_active_user),
    session=Depends(get_db),
):
    user_id = uuid.UUID(current_user["sub"])
    return await DeleteInsuranceUseCase(session).execute(user_id, insurance_id)


@router.patch("/{insurance_id}/status")
async def update_insurance_status(
    insurance_id: uuid.UUID,
    body: dict,
    current_user: dict = Depends(get_current_active_user),
    session=Depends(get_db),
):
    user_id = uuid.UUID(current_user["sub"])
    return await UpdateInsuranceStatusUseCase(session).execute(
        user_id, insurance_id, body.get("status", "")
    )


@router.post("/{insurance_id}/policies", status_code=201)
async def create_policy(
    insurance_id: uuid.UUID,
    body: dict,
    current_user: dict = Depends(get_current_active_user),
    session=Depends(get_db),
):
    user_id = uuid.UUID(current_user["sub"])
    return await CreatePolicyUseCase(session).execute(
        user_id=user_id,
        insurance_id=insurance_id,
        name=body.get("name", ""),
        description=body.get("description"),
        coverage_details=body.get("coverage_details"),
        deductible=body.get("deductible"),
    )


@router.get("/{insurance_id}/policies")
async def list_policies(
    insurance_id: uuid.UUID,
    current_user: dict = Depends(get_current_active_user),
    session=Depends(get_db),
):
    user_id = uuid.UUID(current_user["sub"])
    return await ListPoliciesUseCase(session).execute(user_id, insurance_id)


@router.delete("/{insurance_id}/policies/{policy_id}")
async def delete_policy(
    insurance_id: uuid.UUID,
    policy_id: uuid.UUID,
    current_user: dict = Depends(get_current_active_user),
    session=Depends(get_db),
):
    user_id = uuid.UUID(current_user["sub"])
    return await DeletePolicyUseCase(session).execute(user_id, insurance_id, policy_id)


@router.post("/{insurance_id}/premiums", status_code=201)
async def create_premium(
    insurance_id: uuid.UUID,
    body: dict,
    current_user: dict = Depends(get_current_active_user),
    session=Depends(get_db),
):
    user_id = uuid.UUID(current_user["sub"])
    return await CreatePremiumUseCase(session).execute(
        user_id=user_id,
        insurance_id=insurance_id,
        amount=body.get("amount", 0),
        due_date=date.fromisoformat(body["due_date"]),
        paid_date=date.fromisoformat(body["paid_date"]) if body.get("paid_date") else None,
        payment_method=body.get("payment_method"),
    )


@router.get("/{insurance_id}/premiums")
async def list_premiums(
    insurance_id: uuid.UUID,
    status: str | None = None,
    current_user: dict = Depends(get_current_active_user),
    session=Depends(get_db),
):
    user_id = uuid.UUID(current_user["sub"])
    return await ListPremiumsUseCase(session).execute(user_id, insurance_id, status=status)


@router.patch("/{insurance_id}/premiums/{premium_id}")
async def mark_premium_paid(
    insurance_id: uuid.UUID,
    premium_id: uuid.UUID,
    body: dict,
    current_user: dict = Depends(get_current_active_user),
    session=Depends(get_db),
):
    user_id = uuid.UUID(current_user["sub"])
    return await MarkPremiumPaidUseCase(session).execute(
        user_id=user_id,
        insurance_id=insurance_id,
        premium_id=premium_id,
        paid_date=date.fromisoformat(body["paid_date"]) if body.get("paid_date") else None,
        payment_method=body.get("payment_method"),
    )


@router.delete("/{insurance_id}/premiums/{premium_id}")
async def delete_premium(
    insurance_id: uuid.UUID,
    premium_id: uuid.UUID,
    current_user: dict = Depends(get_current_active_user),
    session=Depends(get_db),
):
    user_id = uuid.UUID(current_user["sub"])
    return await DeletePremiumUseCase(session).execute(user_id, insurance_id, premium_id)
