"""Investment domain value objects tests."""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.domain.investment.value_objects import (
    ASSET_TYPES,
    INVESTMENT_TX_TYPES,
    AssetType,
    Currency,
    InvestmentTxType,
    PortfolioSummary,
)


@pytest.mark.unit
class TestAssetType:
    def test_valid_asset_type(self) -> None:
        for key in ASSET_TYPES:
            assert AssetType(key).value == key

    def test_normalizes_to_lowercase(self) -> None:
        assert AssetType("ETF").value == "etf"

    def test_invalid_asset_type(self) -> None:
        with pytest.raises(ValueError, match="no soportado"):
            AssetType("forex")

    def test_spanish_label(self) -> None:
        assert AssetType("crypto").name == "Criptomoneda"
        assert AssetType("stock").name == "Accion"

    def test_str_returns_value(self) -> None:
        assert str(AssetType("bond")) == "bond"


@pytest.mark.unit
class TestInvestmentTxType:
    def test_valid_tx_types(self) -> None:
        for key in INVESTMENT_TX_TYPES:
            assert InvestmentTxType(key).value == key

    def test_invalid_tx_type(self) -> None:
        with pytest.raises(ValueError, match="no soportado"):
            InvestmentTxType("short")

    def test_spanish_label(self) -> None:
        assert InvestmentTxType("buy").name == "Compra"
        assert InvestmentTxType("dividend").name == "Dividendo"


@pytest.mark.unit
class TestCurrency:
    def test_valid_currency(self) -> None:
        assert Currency("usd").value == "USD"

    def test_invalid_currency(self) -> None:
        with pytest.raises(ValueError, match="Moneda no soportada"):
            Currency("XXX")


@pytest.mark.unit
class TestPortfolioSummary:
    def test_as_dict_quantizes(self) -> None:
        summary = PortfolioSummary(
            total_value=Decimal("1234.567"),
            total_cost=Decimal("1000"),
            gain_loss=Decimal("234.567"),
            gain_loss_percent=Decimal("23.4567"),
            asset_allocation={"stock": Decimal("1234.567")},
        )
        data = summary.as_dict()
        assert data["total_value"] == 1234.57
        assert data["total_cost"] == 1000.0
        assert data["gain_loss"] == 234.57
        assert data["gain_loss_percent"] == 23.46
        assert data["asset_allocation"] == {"stock": 1234.57}
