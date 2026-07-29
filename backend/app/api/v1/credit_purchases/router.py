from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends

from app.api.deps import get_current_active_user, get_db
from app.api.v1.credit_purchases.schemas import (
    CreateCreditPurchaseSchema,
    SimulateCreditPurchaseSchema,
    UpdateCreditPurchaseSchema,
)
from app.application.credit_purchases.create_credit_purchase import CreateCreditPurchaseUseCase
from app.application.credit_purchases.delete_credit_purchase import DeleteCreditPurchaseUseCase
from app.application.credit_purchases.get_credit_purchase import GetCreditPurchaseUseCase
from app.application.credit_purchases.list_credit_purchases import ListCreditPurchasesUseCase
from app.application.credit_purchases.mark_installment_paid import MarkInstallmentPaidUseCase
from app.application.credit_purchases.simulate_credit_purchase import SimulateCreditPurchaseUseCase
from app.application.credit_purchases.update_credit_purchase import UpdateCreditPurchaseUseCase

router = APIRouter(prefix="/credit-purchases", tags=["Credit Purchases"])


@router.post("", status_code=201)
async def create_credit_purchase(
    body: CreateCreditPurchaseSchema,
    current_user: dict = Depends(get_current_active_user),
    session=Depends(get_db),
):
    user_id = uuid.UUID(current_user["sub"])
    return await CreateCreditPurchaseUseCase(session).execute(
        user_id=user_id,
        item_name=body.item_name,
        total_price=body.total_price,
        store_name=body.store_name,
        description=body.description,
        down_payment=body.down_payment,
        annual_interest_rate=body.annual_interest_rate,
        installment_count=body.installment_count,
        installment_frequency=body.installment_frequency,
        installment_amount=body.installment_amount,
        purchase_date=body.purchase_date,
        first_due_date=body.first_due_date,
        notes=body.notes,
    )


@router.get("")
async def list_credit_purchases(
    status: str | None = None,
    current_user: dict = Depends(get_current_active_user),
    session=Depends(get_db),
):
    user_id = uuid.UUID(current_user["sub"])
    return await ListCreditPurchasesUseCase(session).execute(user_id, status=status)


@router.post("/simulate")
async def simulate_credit_purchase(
    body: SimulateCreditPurchaseSchema,
    current_user: dict = Depends(get_current_active_user),
):
    return await SimulateCreditPurchaseUseCase().execute(
        total_price=body.total_price,
        down_payment=body.down_payment,
        annual_interest_rate=body.annual_interest_rate,
        installment_count=body.installment_count,
        installment_frequency=body.installment_frequency,
        installment_amount=body.installment_amount,
        first_due_date=body.first_due_date,
    )


@router.get("/{purchase_id}")
async def get_credit_purchase(
    purchase_id: uuid.UUID,
    current_user: dict = Depends(get_current_active_user),
    session=Depends(get_db),
):
    user_id = uuid.UUID(current_user["sub"])
    return await GetCreditPurchaseUseCase(session).execute(user_id, purchase_id)


@router.patch("/{purchase_id}")
async def update_credit_purchase(
    purchase_id: uuid.UUID,
    body: UpdateCreditPurchaseSchema,
    current_user: dict = Depends(get_current_active_user),
    session=Depends(get_db),
):
    user_id = uuid.UUID(current_user["sub"])
    data = body.model_dump(exclude_unset=True)
    return await UpdateCreditPurchaseUseCase(session).execute(user_id, purchase_id, data)


@router.delete("/{purchase_id}")
async def delete_credit_purchase(
    purchase_id: uuid.UUID,
    current_user: dict = Depends(get_current_active_user),
    session=Depends(get_db),
):
    user_id = uuid.UUID(current_user["sub"])
    return await DeleteCreditPurchaseUseCase(session).execute(user_id, purchase_id)


@router.post("/{purchase_id}/installments/{installment_id}/pay")
async def mark_installment_paid(
    purchase_id: uuid.UUID,
    installment_id: uuid.UUID,
    current_user: dict = Depends(get_current_active_user),
    session=Depends(get_db),
):
    user_id = uuid.UUID(current_user["sub"])
    return await MarkInstallmentPaidUseCase(session).execute(
        user_id=user_id,
        purchase_id=purchase_id,
        installment_id=installment_id,
    )
