"""Plaid endpoints: vinculacion de cuentas bancarias."""

from __future__ import annotations

import uuid
from datetime import date

from fastapi import APIRouter, Depends

from app.api.deps import get_current_active_user, get_db
from app.application.plaid.create_link_token import CreateLinkTokenUseCase
from app.application.plaid.delete_item import DeletePlaidItemUseCase
from app.application.plaid.exchange_public_token import ExchangePublicTokenUseCase
from app.application.plaid.get_item import GetPlaidItemUseCase
from app.application.plaid.get_plaid_status import GetPlaidStatusUseCase
from app.application.plaid.get_transactions import GetPlaidTransactionsUseCase
from app.application.plaid.list_items import ListPlaidItemsUseCase

router = APIRouter(prefix="/plaid", tags=["Plaid"])


@router.get("/status")
async def plaid_status(
    current_user: dict = Depends(get_current_active_user),
):
    uuid.UUID(current_user["sub"])
    return GetPlaidStatusUseCase().execute()


@router.post("/link-token")
async def create_link_token(
    body: dict,
    current_user: dict = Depends(get_current_active_user),
):
    user_id = uuid.UUID(current_user["sub"])
    return await CreateLinkTokenUseCase().execute(
        user_id=user_id,
        redirect_uri=body.get("redirect_uri"),
    )


@router.post("/exchange-token")
async def exchange_public_token(
    body: dict,
    current_user: dict = Depends(get_current_active_user),
    session=Depends(get_db),
):
    user_id = uuid.UUID(current_user["sub"])
    return await ExchangePublicTokenUseCase(session).execute(
        user_id=user_id,
        public_token=body.get("public_token", ""),
    )


@router.get("/items")
async def list_items(
    current_user: dict = Depends(get_current_active_user),
    session=Depends(get_db),
):
    user_id = uuid.UUID(current_user["sub"])
    return await ListPlaidItemsUseCase(session).execute(user_id)


@router.get("/items/{item_id}")
async def get_item(
    item_id: uuid.UUID,
    current_user: dict = Depends(get_current_active_user),
    session=Depends(get_db),
):
    user_id = uuid.UUID(current_user["sub"])
    return await GetPlaidItemUseCase(session).execute(user_id, item_id)


@router.delete("/items/{item_id}")
async def delete_item(
    item_id: uuid.UUID,
    current_user: dict = Depends(get_current_active_user),
    session=Depends(get_db),
):
    user_id = uuid.UUID(current_user["sub"])
    return await DeletePlaidItemUseCase(session).execute(user_id, item_id)


@router.get("/items/{item_id}/transactions")
async def get_transactions(
    item_id: uuid.UUID,
    start_date: str,
    end_date: str,
    current_user: dict = Depends(get_current_active_user),
    session=Depends(get_db),
):
    user_id = uuid.UUID(current_user["sub"])
    return await GetPlaidTransactionsUseCase(session).execute(
        user_id=user_id,
        item_id=item_id,
        start_date=date.fromisoformat(start_date),
        end_date=date.fromisoformat(end_date),
    )
