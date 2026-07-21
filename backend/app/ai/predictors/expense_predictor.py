"""Expense/Income prediction using XGBoost."""

from __future__ import annotations

import time
from pathlib import Path

import joblib
import numpy as np
import structlog
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.features.feature_extractor import MONTHLY_FEATURE_NAMES, extract_monthly_features
from app.infrastructure.models.transaction import TransactionModel

logger = structlog.get_logger()
MODEL_DIR = Path("backend/ai_models")


class ExpensePredictor:
    def __init__(self) -> None:
        self._model = None
        self._scaler = None
        self._is_trained = False
        self._model_version = "xgb_expense_v1.0"
        self._target_type: str = "expense"

    @property
    def is_trained(self) -> bool:
        return self._is_trained

    @property
    def model_version(self) -> str:
        return self._model_version

    async def train(self, session: AsyncSession, user_id, *, target_type: str = "expense") -> dict:
        start_time = time.time()
        self._target_type = target_type
        from datetime import date, timedelta

        from sklearn.preprocessing import StandardScaler
        from xgboost import XGBRegressor

        stmt = (
            select(TransactionModel)
            .where(
                and_(
                    TransactionModel.user_id == user_id,
                    TransactionModel.deleted_at.is_(None),
                    TransactionModel.status == "completed",
                    TransactionModel.transaction_type.in_(["expense", "income"]),
                )
            )
            .order_by(TransactionModel.effective_date.asc())
        )
        result = await session.execute(stmt)
        transactions = list(result.scalars().all())

        if len(transactions) < 10:
            return {
                "accuracy": 0.0,
                "samples": 0,
                "error": "Need at least 10 transactions",
                "duration_seconds": 0.0,
            }

        monthly_data: dict[str, list[dict]] = {}
        for tx in transactions:
            month_key = tx.effective_date.strftime("%Y-%m")
            if month_key not in monthly_data:
                monthly_data[month_key] = []
            monthly_data[month_key].append(
                {
                    "amount": float(tx.amount),
                    "transaction_type": tx.transaction_type,
                    "effective_date": tx.effective_date.isoformat(),
                    "category_name": tx.category.name if tx.category else None,
                }
            )

        sorted_months = sorted(monthly_data.keys())
        if len(sorted_months) < 3:
            return {
                "accuracy": 0.0,
                "samples": 0,
                "error": "Need at least 3 months",
                "duration_seconds": 0.0,
            }

        X, y = [], []
        for i in range(1, len(sorted_months)):
            prev_features = extract_monthly_features(monthly_data[sorted_months[i - 1]])
            feature_vector = [prev_features.get(name, 0.0) for name in MONTHLY_FEATURE_NAMES]
            curr_txs = monthly_data[sorted_months[i]]
            target = sum(
                abs(float(t["amount"])) for t in curr_txs if t["transaction_type"] == target_type
            )
            X.append(feature_vector)
            y.append(target)

        X_array = np.array(X, dtype=np.float32)
        y_array = np.array(y, dtype=np.float32)

        self._scaler = StandardScaler()
        X_scaled = self._scaler.fit_transform(X_array)

        self._model = XGBRegressor(
            n_estimators=100, max_depth=4, learning_rate=0.1, random_state=42, verbosity=0
        )

        from sklearn.model_selection import cross_val_score

        if len(X_scaled) >= 4:
            scores = cross_val_score(
                self._model, X_scaled, y_array, cv=min(3, len(X_scaled)), scoring="r2"
            )
            cv_r2 = float(np.mean(scores))
        else:
            cv_r2 = 0.0

        self._model.fit(X_scaled, y_array)
        y_pred = self._model.predict(X_scaled)
        mse = float(np.mean((y_array - y_pred) ** 2))
        mae = float(np.mean(np.abs(y_array - y_pred)))
        r2_var = float(np.var(y_array))
        r2 = (
            float(1 - (np.sum((y_array - y_pred) ** 2) / np.sum((y_array - np.mean(y_array)) ** 2)))
            if r2_var > 0
            else 0.0
        )

        duration = time.time() - start_time
        self._is_trained = True
        self._save_model(str(user_id))

        return {
            "r2": round(max(r2, 0.0), 4),
            "cv_r2": round(max(cv_r2, 0.0), 4),
            "mse": round(mse, 2),
            "mae": round(mae, 2),
            "samples": len(X),
            "months_used": len(sorted_months),
            "duration_seconds": round(duration, 2),
        }

    async def predict(self, session: AsyncSession, user_id, *, months_ahead: int = 1) -> dict:
        if not self._is_trained:
            return {
                "predicted_amount": 0.0,
                "confidence": 0.0,
                "model_version": "none",
                "reason": "Model not trained yet.",
                "features_used": {},
            }

        from datetime import date, timedelta

        today = date.today()
        month_start = today.replace(day=1)
        prev_month_end = month_start - timedelta(days=1)
        prev_month_start = prev_month_end.replace(day=1)

        stmt = select(TransactionModel).where(
            and_(
                TransactionModel.user_id == user_id,
                TransactionModel.deleted_at.is_(None),
                TransactionModel.status == "completed",
                TransactionModel.transaction_type.in_(["expense", "income"]),
                TransactionModel.effective_date >= prev_month_start,
                TransactionModel.effective_date <= prev_month_end,
            )
        )
        result = await session.execute(stmt)
        txs = list(result.scalars().all())

        tx_dicts = [
            {
                "amount": float(tx.amount),
                "transaction_type": tx.transaction_type,
                "effective_date": tx.effective_date.isoformat(),
                "category_name": tx.category.name if tx.category else None,
            }
            for tx in txs
        ]

        features = extract_monthly_features(tx_dicts)
        feature_vector = np.array(
            [[features.get(name, 0.0) for name in MONTHLY_FEATURE_NAMES]], dtype=np.float32
        )
        if self._scaler:
            feature_vector = self._scaler.transform(feature_vector)

        predicted_amount = max(float(self._model.predict(feature_vector)[0]), 0.0)
        confidence = (
            min(0.9, 0.3 + (features["total_transactions"] / 100))
            if features["total_transactions"] > 0
            else 0.5
        )

        return {
            "predicted_amount": round(predicted_amount, 2),
            "confidence": round(confidence, 4),
            "model_version": self._model_version,
            "features_used": features,
            "reason": f"Prediccion basada en {features['total_transactions']} transacciones del mes anterior.",
        }

    def _save_model(self, user_id: str) -> None:
        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        path = MODEL_DIR / f"{self._target_type}_predictor_{user_id}.joblib"
        joblib.dump(
            {
                "model": self._model,
                "scaler": self._scaler,
                "version": self._model_version,
                "target_type": self._target_type,
            },
            path,
        )
        logger.info("predictor_saved", path=str(path), target_type=self._target_type)

    def load_model(self, user_id: str) -> bool:
        path = MODEL_DIR / f"{self._target_type}_predictor_{user_id}.joblib"
        if not path.exists():
            return False
        try:
            data = joblib.load(path)
            self._model = data["model"]
            self._scaler = data["scaler"]
            self._model_version = data.get("version", "xgb_expense_v1.0")
            self._target_type = data.get("target_type", "expense")
            self._is_trained = True
            return True
        except Exception as e:
            logger.error("predictor_load_failed", error=str(e))
            return False
