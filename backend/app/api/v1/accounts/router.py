"""Accounts API router — Financial account management."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

import structlog
from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_active_user, get_db
from app.api.v1.accounts.schemas import (
    AccountResponse,
    AccountSummaryResponse,
    CreateAccountRequest,
    DeleteAccountResponse,
    ListAccountsResponse,
    UpdateAccountRequest,
    UpdateAccountResponse,
)
from app.application.accounts.create_account import CreateAccountUseCase
from app.application.accounts.delete_account import DeleteAccountUseCase
from app.application.accounts.get_account import GetAccountUseCase
from app.application.accounts.get_account_summary import GetAccountSummaryUseCase
from app.application.accounts.list_accounts import ListAccountsUseCase
from app.application.accounts.update_account import UpdateAccountUseCase

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()

router = APIRouter(prefix="/accounts", tags=["Financial Accounts"])


# ============================================================
# Create Account
# ============================================================


@router.post(
    "",
    response_model=AccountResponse,
    status_code=201,
    summary="Create a new financial account",
    description="Create a bank, cash, savings, checking, wallet, or crypto account.",
)
async def create_account(
    body: CreateAccountRequest,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Create a new financial account."""
    user_id = uuid.UUID(current_user["sub"])
    fields = body.model_dump(exclude_unset=True)
    use_case = CreateAccountUseCase(db)
    result = await use_case.execute(user_id, **fields)
    return result


# ============================================================
# List Accounts
# ============================================================


@router.get(
    "",
    response_model=ListAccountsResponse,
    summary="List financial accounts",
    description="List all accounts for the authenticated user. Filter by type or include archived.",
)
async def list_accounts(
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    account_type: str | None = Query(None, description="Filter by type: bank, cash, etc."),
    include_archived: bool = Query(False, description="Include archived accounts"),
) -> dict:
    """List all financial accounts."""
    user_id = uuid.UUID(current_user["sub"])
    use_case = ListAccountsUseCase(db)
    accounts = await use_case.execute(
        user_id,
        account_type=account_type,
        include_archived=include_archived,
    )
    return {"accounts": accounts, "total": len(accounts)}


# ============================================================
# Get Account Summary
# ============================================================


@router.get(
    "/summary",
    response_model=AccountSummaryResponse,
    summary="Get account summary",
    description="Aggregated totals by currency across all active accounts.",
)
async def get_account_summary(
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get aggregated account summary."""
    user_id = uuid.UUID(current_user["sub"])
    use_case = GetAccountSummaryUseCase(db)
    return await use_case.execute(user_id)


# ============================================================
# Get Single Account
# ============================================================


@router.get(
    "/{account_id}",
    response_model=AccountResponse,
    summary="Get account details",
    description="Get full details of a single financial account.",
)
async def get_account(
    account_id: uuid.UUID,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get a single financial account."""
    user_id = uuid.UUID(current_user["sub"])
    use_case = GetAccountUseCase(db)
    return await use_case.execute(user_id, account_id)


# ============================================================
# Update Account
# ============================================================


@router.patch(
    "/{account_id}",
    response_model=UpdateAccountResponse,
    summary="Update account",
    description="Partial update of account fields.",
)
async def update_account(
    account_id: uuid.UUID,
    body: UpdateAccountRequest,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Update a financial account (partial)."""
    user_id = uuid.UUID(current_user["sub"])
    fields = body.model_dump(exclude_unset=True, exclude_none=True)
    use_case = UpdateAccountUseCase(db)
    await use_case.execute(user_id, account_id, **fields)
    return {"message": "Account updated successfully"}


# ============================================================
# Delete Account (soft-delete)
# ============================================================


@router.delete(
    "/{account_id}",
    response_model=DeleteAccountResponse,
    summary="Delete account",
    description="Soft-delete a financial account. Sets status to archived and deleted_at.",
)
async def delete_account(
    account_id: uuid.UUID,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Soft-delete a financial account."""
    user_id = uuid.UUID(current_user["sub"])
    use_case = DeleteAccountUseCase(db)
    return await use_case.execute(user_id, account_id)
