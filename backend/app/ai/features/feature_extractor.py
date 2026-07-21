"""Feature engineering for ML models."""
from __future__ import annotations

import math
import re
from datetime import date
from typing import Any


def extract_transaction_features(
    *,
    description: str,
    amount: float,
    transaction_type: str,
    effective_date: date | str,
    category_name: str | None = None,
    subcategory_name: str | None = None,
    account_type: str | None = None,
    day_of_week: int | None = None,
) -> dict[str, Any]:
    """Extract features from a single transaction."""
    if isinstance(effective_date, str):
        dt = date.fromisoformat(effective_date)
    else:
        dt = effective_date
    if day_of_week is None:
        day_of_week = dt.weekday()
    desc_clean = _preprocess_text(description)
    return {
        "amount": float(amount),
        "amount_log": _safe_log(float(amount)),
        "amount_round": 1.0 if float(amount) == int(float(amount)) else 0.0,
        "is_round_amount": 1.0 if float(amount) % 100 == 0 else 0.0,
        "day_of_week": day_of_week,
        "day_of_month": dt.day,
        "month": dt.month,
        "quarter": (dt.month - 1) // 3 + 1,
        "is_weekend": 1.0 if day_of_week >= 5 else 0.0,
        "is_month_start": 1.0 if dt.day <= 7 else 0.0,
        "is_month_end": 1.0 if dt.day >= 25 else 0.0,
        "is_quarter_end": 1.0 if dt.month in (3, 6, 9, 12) and dt.day >= 28 else 0.0,
        "description_length": len(desc_clean),
        "description_word_count": len(desc_clean.split()),
        "has_number_in_desc": 1.0 if re.search(r"\d", description) else 0.0,
        "has_uppercase_in_desc": 1.0 if re.search(r"[A-Z]{2,}", description) else 0.0,
        "category_encoded": _hash_category(category_name),
        "subcategory_encoded": _hash_category(subcategory_name),
        "is_expense": 1.0 if transaction_type == "expense" else 0.0,
        "is_income": 1.0 if transaction_type == "income" else 0.0,
        "is_transfer": 1.0 if transaction_type == "transfer" else 0.0,
        "account_type_encoded": _hash_category(account_type),
    }


def extract_monthly_features(transactions: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate transaction features into monthly-level features."""
    if not transactions:
        return _empty_monthly_features()
    amounts = [abs(float(t.get("amount", 0))) for t in transactions]
    expense_amounts = [
        abs(float(t.get("amount", 0)))
        for t in transactions
        if t.get("transaction_type") == "expense"
    ]
    income_amounts = [
        float(t.get("amount", 0)) for t in transactions if t.get("transaction_type") == "income"
    ]
    days: set[int] = set()
    categories: set[str] = set()
    for t in transactions:
        ed = t.get("effective_date")
        if isinstance(ed, str):
            days.add(date.fromisoformat(ed).day)
        elif isinstance(ed, date):
            days.add(ed.day)
        cat = t.get("category_name")
        if cat:
            categories.add(cat)
    return {
        "total_transactions": len(transactions),
        "total_amount": sum(amounts),
        "avg_amount": sum(amounts) / len(amounts) if amounts else 0.0,
        "max_amount": max(amounts) if amounts else 0.0,
        "min_amount": min(amounts) if amounts else 0.0,
        "std_amount": _std(amounts),
        "expense_count": len(expense_amounts),
        "expense_total": sum(expense_amounts),
        "expense_avg": sum(expense_amounts) / len(expense_amounts) if expense_amounts else 0.0,
        "expense_max": max(expense_amounts) if expense_amounts else 0.0,
        "income_count": len(income_amounts),
        "income_total": sum(income_amounts),
        "income_avg": sum(income_amounts) / len(income_amounts) if income_amounts else 0.0,
        "income_max": max(income_amounts) if income_amounts else 0.0,
        "unique_days_active": len(days),
        "unique_categories": len(categories),
        "expense_to_income_ratio": sum(expense_amounts) / sum(income_amounts)
        if income_amounts and sum(income_amounts) > 0
        else 0.0,
    }


def _preprocess_text(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s]", " ", text)
    return re.sub(r"\s+", " ", text)


def _safe_log(value: float) -> float:
    return math.log(value) if value > 0 else 0.0


def _hash_category(name: str | None) -> float:
    if not name:
        return 0.0
    return float(hash(name.lower()) % 10000) / 10000.0


def _std(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    return math.sqrt(sum((x - mean) ** 2 for x in values) / (len(values) - 1))


def _empty_monthly_features() -> dict[str, Any]:
    return {
        "total_transactions": 0,
        "total_amount": 0.0,
        "avg_amount": 0.0,
        "max_amount": 0.0,
        "min_amount": 0.0,
        "std_amount": 0.0,
        "expense_count": 0,
        "expense_total": 0.0,
        "expense_avg": 0.0,
        "expense_max": 0.0,
        "income_count": 0,
        "income_total": 0.0,
        "income_avg": 0.0,
        "income_max": 0.0,
        "unique_days_active": 0,
        "unique_categories": 0,
        "expense_to_income_ratio": 0.0,
    }


MONTHLY_FEATURE_NAMES: list[str] = [
    "total_transactions",
    "total_amount",
    "avg_amount",
    "max_amount",
    "min_amount",
    "std_amount",
    "expense_count",
    "expense_total",
    "expense_avg",
    "expense_max",
    "income_count",
    "income_total",
    "income_avg",
    "income_max",
    "unique_days_active",
    "unique_categories",
    "expense_to_income_ratio",
]

TRANSACTION_FEATURE_NAMES: list[str] = [
    "amount",
    "amount_log",
    "amount_round",
    "is_round_amount",
    "day_of_week",
    "day_of_month",
    "month",
    "quarter",
    "is_weekend",
    "is_month_start",
    "is_month_end",
    "is_quarter_end",
    "description_length",
    "description_word_count",
    "has_number_in_desc",
    "has_uppercase_in_desc",
    "category_encoded",
    "subcategory_encoded",
    "is_expense",
    "is_income",
    "is_transfer",
    "account_type_encoded",
]
