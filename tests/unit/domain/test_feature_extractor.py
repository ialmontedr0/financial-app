"""Unit tests for feature extraction."""

from datetime import date

from app.ai.features.feature_extractor import (
    MONTHLY_FEATURE_NAMES,
    TRANSACTION_FEATURE_NAMES,
    extract_monthly_features,
    extract_transaction_features,
)


class TestTransactionFeatures:
    def test_basic_features(self):
        features = extract_transaction_features(
            description="Supermercado Nacional",
            amount=1500.0,
            transaction_type="expense",
            effective_date=date(2025, 1, 15),
            category_name="food",
        )
        assert features["amount"] == 1500.0
        assert features["is_expense"] == 1.0
        assert features["is_income"] == 0.0
        assert features["day_of_week"] == 2  # Wednesday
        assert features["month"] == 1
        assert features["quarter"] == 1

    def test_weekend_detection(self):
        features = extract_transaction_features(
            description="Restaurant",
            amount=500.0,
            transaction_type="expense",
            effective_date=date(2025, 1, 18),  # Saturday
        )
        assert features["is_weekend"] == 1.0

    def test_month_end(self):
        features = extract_transaction_features(
            description="Rent",
            amount=25000.0,
            transaction_type="expense",
            effective_date=date(2025, 1, 28),
        )
        assert features["is_month_end"] == 1.0

    def test_feature_count(self):
        features = extract_transaction_features(
            description="Test",
            amount=100.0,
            transaction_type="expense",
            effective_date=date(2025, 1, 1),
        )
        assert len(features) == len(TRANSACTION_FEATURE_NAMES)


class TestMonthlyFeatures:
    def test_empty_transactions(self):
        features = extract_monthly_features([])
        assert features["total_transactions"] == 0
        assert features["expense_total"] == 0.0

    def test_basic_aggregation(self):
        txs = [
            {
                "amount": 1000,
                "transaction_type": "expense",
                "effective_date": "2025-01-05",
                "category_name": "food",
            },
            {
                "amount": 500,
                "transaction_type": "expense",
                "effective_date": "2025-01-15",
                "category_name": "transport",
            },
            {
                "amount": 5000,
                "transaction_type": "income",
                "effective_date": "2025-01-01",
                "category_name": None,
            },
        ]
        features = extract_monthly_features(txs)
        assert features["total_transactions"] == 3
        assert features["expense_count"] == 2
        assert features["expense_total"] == 1500.0
        assert features["income_count"] == 1
        assert features["income_total"] == 5000.0
        assert features["unique_categories"] == 2
