"""Investment endpoints."""

from __future__ import annotations

import uuid
from datetime import date

from fastapi import APIRouter, Depends

from app.api.deps import get_current_active_user, get_db
from app.api.v1.investments.schemas import (
    AddPricePointSchema,
    CreateAssetSchema,
    CreateInvestmentTransactionSchema,
    CreatePortfolioSchema,
    UpdateAssetPriceSchema,
)
from app.application.investment.add_price_point import AddPricePointUseCase
from app.application.investment.create_asset import CreateAssetUseCase
from app.application.investment.create_investment_transaction import (
    CreateInvestmentTransactionUseCase,
)
from app.application.investment.create_portfolio import CreatePortfolioUseCase
from app.application.investment.delete_asset import DeleteAssetUseCase
from app.application.investment.delete_portfolio import DeletePortfolioUseCase
from app.application.investment.get_asset import GetAssetUseCase
from app.application.investment.get_asset_price_history import GetAssetPriceHistoryUseCase
from app.application.investment.get_portfolio import GetPortfolioUseCase
from app.application.investment.get_portfolio_summary import GetPortfolioSummaryUseCase
from app.application.investment.list_assets import ListAssetsUseCase
from app.application.investment.list_portfolios import ListPortfoliosUseCase
from app.application.investment.list_transactions import ListTransactionsUseCase
from app.application.investment.update_asset_price import UpdateAssetPriceUseCase

router = APIRouter(prefix="/investments", tags=["Investments"])


# ── Portfolio summary ──────────────────────────────────────────


@router.get("/portfolio")
async def get_portfolio_summary(
    current_user: dict = Depends(get_current_active_user),
    session=Depends(get_db),
):
    user_id = uuid.UUID(current_user["sub"])
    return await GetPortfolioSummaryUseCase(session).execute(user_id)


# ── Assets ─────────────────────────────────────────────────────


@router.post("/assets", status_code=201)
async def create_asset(
    body: CreateAssetSchema,
    current_user: dict = Depends(get_current_active_user),
    session=Depends(get_db),
):
    user_id = uuid.UUID(current_user["sub"])
    return await CreateAssetUseCase(session).execute(
        user_id=user_id,
        name=body.name,
        asset_type=body.asset_type,
        currency=body.currency,
        symbol=body.symbol,
        current_price=body.current_price,
    )


@router.get("/assets")
async def list_assets(
    current_user: dict = Depends(get_current_active_user),
    session=Depends(get_db),
):
    user_id = uuid.UUID(current_user["sub"])
    return await ListAssetsUseCase(session).execute(user_id)


@router.get("/assets/{asset_id}")
async def get_asset(
    asset_id: uuid.UUID,
    current_user: dict = Depends(get_current_active_user),
    session=Depends(get_db),
):
    user_id = uuid.UUID(current_user["sub"])
    return await GetAssetUseCase(session).execute(user_id, asset_id)


@router.patch("/assets/{asset_id}")
async def update_asset_price(
    asset_id: uuid.UUID,
    body: UpdateAssetPriceSchema,
    current_user: dict = Depends(get_current_active_user),
    session=Depends(get_db),
):
    user_id = uuid.UUID(current_user["sub"])
    return await UpdateAssetPriceUseCase(session).execute(user_id, asset_id, body.current_price)


@router.delete("/assets/{asset_id}")
async def delete_asset(
    asset_id: uuid.UUID,
    current_user: dict = Depends(get_current_active_user),
    session=Depends(get_db),
):
    user_id = uuid.UUID(current_user["sub"])
    return await DeleteAssetUseCase(session).execute(user_id, asset_id)


@router.get("/assets/{asset_id}/price-history")
async def get_asset_price_history(
    asset_id: uuid.UUID,
    limit: int = 90,
    current_user: dict = Depends(get_current_active_user),
    session=Depends(get_db),
):
    user_id = uuid.UUID(current_user["sub"])
    return await GetAssetPriceHistoryUseCase(session).execute(user_id, asset_id, limit=limit)


@router.post("/assets/{asset_id}/price-history", status_code=201)
async def add_price_point(
    asset_id: uuid.UUID,
    body: AddPricePointSchema,
    current_user: dict = Depends(get_current_active_user),
    session=Depends(get_db),
):
    user_id = uuid.UUID(current_user["sub"])
    return await AddPricePointUseCase(session).execute(
        user_id=user_id,
        asset_id=asset_id,
        close_price=body.close_price,
        price_date=date.fromisoformat(body.date) if body.date else None,
        open_price=body.open_price,
        high_price=body.high_price,
        low_price=body.low_price,
        volume=body.volume,
    )


@router.post("/assets/{asset_id}/transactions", status_code=201)
async def create_investment_transaction(
    asset_id: uuid.UUID,
    body: CreateInvestmentTransactionSchema,
    current_user: dict = Depends(get_current_active_user),
    session=Depends(get_db),
):
    user_id = uuid.UUID(current_user["sub"])
    return await CreateInvestmentTransactionUseCase(session).execute(
        user_id=user_id,
        asset_id=asset_id,
        tx_type=body.type,
        quantity=body.quantity,
        price_per_unit=body.price_per_unit,
        fees=body.fees,
        portfolio_id=uuid.UUID(body.portfolio_id) if body.portfolio_id else None,
        tx_date=date.fromisoformat(body.date) if body.date else None,
        total_amount=body.total_amount,
        notes=body.notes,
    )


@router.get("/assets/{asset_id}/transactions")
async def list_asset_transactions(
    asset_id: uuid.UUID,
    current_user: dict = Depends(get_current_active_user),
    session=Depends(get_db),
):
    user_id = uuid.UUID(current_user["sub"])
    return await ListTransactionsUseCase(session).execute(user_id, asset_id=asset_id)


# ── Portfolios ─────────────────────────────────────────────────


@router.post("/portfolios", status_code=201)
async def create_portfolio(
    body: CreatePortfolioSchema,
    current_user: dict = Depends(get_current_active_user),
    session=Depends(get_db),
):
    user_id = uuid.UUID(current_user["sub"])
    return await CreatePortfolioUseCase(session).execute(
        user_id=user_id, name=body.name, description=body.description
    )


@router.get("/portfolios")
async def list_portfolios(
    current_user: dict = Depends(get_current_active_user),
    session=Depends(get_db),
):
    user_id = uuid.UUID(current_user["sub"])
    return await ListPortfoliosUseCase(session).execute(user_id)


@router.get("/portfolios/{portfolio_id}")
async def get_portfolio(
    portfolio_id: uuid.UUID,
    current_user: dict = Depends(get_current_active_user),
    session=Depends(get_db),
):
    user_id = uuid.UUID(current_user["sub"])
    return await GetPortfolioUseCase(session).execute(user_id, portfolio_id)


@router.delete("/portfolios/{portfolio_id}")
async def delete_portfolio(
    portfolio_id: uuid.UUID,
    current_user: dict = Depends(get_current_active_user),
    session=Depends(get_db),
):
    user_id = uuid.UUID(current_user["sub"])
    return await DeletePortfolioUseCase(session).execute(user_id, portfolio_id)


@router.get("/portfolios/{portfolio_id}/transactions")
async def list_portfolio_transactions(
    portfolio_id: uuid.UUID,
    current_user: dict = Depends(get_current_active_user),
    session=Depends(get_db),
):
    user_id = uuid.UUID(current_user["sub"])
    return await ListTransactionsUseCase(session).execute(user_id, portfolio_id=portfolio_id)
