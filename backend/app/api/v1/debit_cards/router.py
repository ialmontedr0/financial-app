"""Debit card management endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_db

router = APIRouter(prefix="/debit-cards", tags=["Debit Cards"])


@router.get("", status_code=200)
async def list_debit_cards(
    account_id: str | None = None,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    from app.application.debit_cards.list_debit_cards import ListDebitCardsUseCase

    return await ListDebitCardsUseCase(db).execute(
        uuid.UUID(current_user["sub"]),
        account_id=uuid.UUID(account_id) if account_id else None,
    )


@router.get("/{card_id}", status_code=200)
async def get_debit_card(
    card_id: uuid.UUID,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    from app.application.debit_cards.get_debit_card import GetDebitCardUseCase

    return await GetDebitCardUseCase(db).execute(uuid.UUID(current_user["sub"]), card_id)


@router.post("", status_code=201)
async def create_debit_card(
    body: dict,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    from app.application.debit_cards.create_debit_card import CreateDebitCardUseCase

    return await CreateDebitCardUseCase(db).execute(uuid.UUID(current_user["sub"]), **body)


@router.patch("/{card_id}", status_code=200)
async def update_debit_card(
    card_id: uuid.UUID,
    body: dict,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    from app.application.debit_cards.update_debit_card import UpdateDebitCardUseCase

    return await UpdateDebitCardUseCase(db).execute(
        uuid.UUID(current_user["sub"]), card_id, changes=body
    )


@router.delete("/{card_id}", status_code=200)
async def delete_debit_card(
    card_id: uuid.UUID,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    from app.application.debit_cards.delete_debit_card import DeleteDebitCardUseCase

    return await DeleteDebitCardUseCase(db).execute(uuid.UUID(current_user["sub"]), card_id)
