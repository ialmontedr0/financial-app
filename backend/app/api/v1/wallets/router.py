"""Wallets API router - Wallet management."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

import structlog
from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_active_user, get_db
from app.api.v1.wallets.schemas import (
    AddAccountRequest,
    AddAccountResponse,
    CreateWalletRequest,
    DeleteWalletResponse,
    ListWalletsResponse,
    RemoveAccountResponse,
    UpdateWalletRequest,
    WalletBalanceResponse,
    WalletDetailResponse,
    WalletLiquidityResponse,
    WalletResponse,
)
from app.application.wallets.add_account import AddAccountToWalletUseCase
from app.application.wallets.create_wallet import CreateWalletUseCase
from app.application.wallets.delete_wallet import DeleteWalletUseCase
from app.application.wallets.get_wallet import GetWalletUseCase
from app.application.wallets.get_wallet_balance import GetWalletBalanceUseCase
from app.application.wallets.get_wallet_liquidity import GetWalletLiquidityUseCase
from app.application.wallets.list_wallets import ListWalletsUseCase
from app.application.wallets.remove_account import RemoveAccountFromWalletUseCase
from app.application.wallets.update_wallet import UpdateWalletUseCase

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()

router = APIRouter(prefix="/wallets", tags=["Wallets"])


@router.post(
    "",
    response_model=WalletResponse,
    status_code=201,
    summary="Create a new wallet",
    description="Create a logical wallet to group financial accounts.",
)
async def create_wallet(
    body: CreateWalletRequest,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Create a new wallet."""
    user_id = uuid.UUID(current_user["sub"])
    fields = body.model_dump(exclude_unset=True)
    use_case = CreateWalletUseCase(db)
    return await use_case.execute(user_id, **fields)


@router.get(
    "",
    response_model=ListWalletsResponse,
    summary="List wallets",
    description="List all wallets for the authenticated user.",
)
async def list_wallets(
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    wallet_type: str | None = Query(None, description="Filter by type"),
) -> dict:
    """List all wallets."""
    user_id = uuid.UUID(current_user["sub"])
    use_case = ListWalletsUseCase(db)
    wallets = await use_case.execute(user_id, wallet_type=wallet_type)
    return {"wallets": wallets, "total": len(wallets)}


@router.get(
    "/{wallet_id}",
    response_model=WalletDetailResponse,
    summary="Get wallet details",
    description="Get full wallet details including linked accounts.",
)
async def get_wallet(
    wallet_id: uuid.UUID,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get a single wallet with linked accounts."""
    user_id = uuid.UUID(current_user["sub"])
    use_case = GetWalletUseCase(db)
    return await use_case.execute(user_id, wallet_id)


@router.patch(
    "/{wallet_id}",
    response_model=WalletResponse,
    summary="Update wallet",
    description="Partial update of wallet fields.",
)
async def update_wallet(
    wallet_id: uuid.UUID,
    body: UpdateWalletRequest,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Update a wallet (partial)."""
    user_id = uuid.UUID(current_user["sub"])
    fields = body.model_dump(exclude_unset=True, exclude_none=True)
    use_case = UpdateWalletUseCase(db)
    return await use_case.execute(user_id, wallet_id, **fields)


@router.delete(
    "/{wallet_id}",
    response_model=DeleteWalletResponse,
    summary="Delete wallet",
    description="Soft-delete a wallet. Linked accounts are NOT deleted.",
)
async def delete_wallet(
    wallet_id: uuid.UUID,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Soft-delete a wallet."""
    user_id = uuid.UUID(current_user["sub"])
    use_case = DeleteWalletUseCase(db)
    return await use_case.execute(user_id, wallet_id)


@router.post(
    "/{wallet_id}/accounts",
    response_model=AddAccountResponse,
    status_code=201,
    summary="Add account to wallet",
    description="Link a financial account to this wallet.",
)
async def add_account(
    wallet_id: uuid.UUID,
    body: AddAccountRequest,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Add a financial account to a wallet."""
    user_id = uuid.UUID(current_user["sub"])
    account_id = uuid.UUID(body.account_id)
    use_case = AddAccountToWalletUseCase(db)
    return await use_case.execute(user_id, wallet_id, account_id, notes=body.notes)


@router.delete(
    "/{wallet_id}/accounts/{account_id}",
    response_model=RemoveAccountResponse,
    summary="Remove account from wallet",
    description="Unlink a financial account from this wallet.",
)
async def remove_account(
    wallet_id: uuid.UUID,
    account_id: uuid.UUID,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Remove a financial account from a wallet."""
    user_id = uuid.UUID(current_user["sub"])
    use_case = RemoveAccountFromWalletUseCase(db)
    return await use_case.execute(user_id, wallet_id, account_id)


@router.get(
    "/{wallet_id}/balance",
    response_model=WalletBalanceResponse,
    summary="Get wallet balance",
    description="Computed balance from all linked active accounts.",
)
async def get_wallet_balance(
    wallet_id: uuid.UUID,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get computed wallet balance."""
    user_id = uuid.UUID(current_user["sub"])
    use_case = GetWalletBalanceUseCase(db)
    return await use_case.execute(user_id, wallet_id)


@router.get(
    "/{wallet_id}/liquidity",
    response_model=WalletLiquidityResponse,
    summary="Get wallet liquidity analysis",
    description="Liquidity breakdown based on account types in the wallet.",
)
async def get_wallet_liquidity(
    wallet_id: uuid.UUID,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get wallet liquidity analysis."""
    user_id = uuid.UUID(current_user["sub"])
    use_case = GetWalletLiquidityUseCase(db)
    return await use_case.execute(user_id, wallet_id)
