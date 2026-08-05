"""Serializers for investment domain models."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from app.infrastructure.models.investment import (
    AssetModel,
    AssetPriceHistoryModel,
    InvestmentTransactionModel,
    PortfolioAssetModel,
    PortfolioModel,
)


def _dec(value: Decimal | None) -> float | None:
    if value is None:
        return None
    return float(value)


def serialize_asset(asset: AssetModel) -> dict[str, Any]:
    return {
        "id": str(asset.id),
        "name": asset.name,
        "symbol": asset.symbol,
        "asset_type": asset.asset_type,
        "currency": asset.currency,
        "current_price": _dec(asset.current_price),
        "created_at": asset.created_at.isoformat() if asset.created_at else None,
    }


def serialize_portfolio(portfolio: PortfolioModel, asset_count: int = 0) -> dict[str, Any]:
    return {
        "id": str(portfolio.id),
        "name": portfolio.name,
        "description": portfolio.description,
        "asset_count": asset_count,
        "created_at": portfolio.created_at.isoformat() if portfolio.created_at else None,
    }


def serialize_portfolio_asset(pa: PortfolioAssetModel, asset: AssetModel | None) -> dict[str, Any]:
    return {
        "asset_id": str(pa.asset_id),
        "name": asset.name if asset else "",
        "symbol": asset.symbol if asset else None,
        "asset_type": asset.asset_type if asset else None,
        "currency": asset.currency if asset else "USD",
        "current_price": _dec(asset.current_price) if asset else None,
        "quantity": float(pa.quantity),
        "cost_basis": _dec(pa.cost_basis),
        "average_price": _dec(pa.average_price),
        "market_value": float(pa.quantity * (asset.current_price or Decimal("0")))
        if asset
        else 0.0,
    }


def serialize_transaction(tx: InvestmentTransactionModel) -> dict[str, Any]:
    return {
        "id": str(tx.id),
        "asset_id": str(tx.asset_id),
        "portfolio_id": str(tx.portfolio_id) if tx.portfolio_id else None,
        "type": tx.type,
        "quantity": float(tx.quantity),
        "price_per_unit": _dec(tx.price_per_unit),
        "total_amount": _dec(tx.total_amount),
        "fees": _dec(tx.fees),
        "date": tx.date.isoformat(),
        "notes": tx.notes,
        "created_at": tx.created_at.isoformat() if tx.created_at else None,
    }


def serialize_price_point(point: AssetPriceHistoryModel) -> dict[str, Any]:
    return {
        "id": str(point.id),
        "asset_id": str(point.asset_id),
        "date": point.date.isoformat(),
        "open_price": _dec(point.open_price),
        "close_price": _dec(point.close_price),
        "high_price": _dec(point.high_price),
        "low_price": _dec(point.low_price),
        "volume": _dec(point.volume),
    }
