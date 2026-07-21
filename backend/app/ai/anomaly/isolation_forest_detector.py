"""Anomaly detection using Isolation Forest."""

from __future__ import annotations

import time
from pathlib import Path

import joblib
import numpy as np
import structlog
from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.features.feature_extractor import (
    TRANSACTION_FEATURE_NAMES,
    extract_transaction_features,
)
from app.infrastructure.models.transaction import TransactionModel

logger = structlog.get_logger()
MODEL_DIR = Path("backend/ai_models")


class IsolationForestDetector:
    def __init__(self) -> None:
        self._model = None
        self._scaler = None
        self._is_trained = False
        self._model_version = "anomaly_iforest_v1.0"
        self._threshold: float = -0.5

    @property
    def is_trained(self) -> bool:
        return self._is_trained

    @property
    def model_version(self) -> str:
        return self._model_version

    async def train(self, session: AsyncSession, user_id, *, contamination: float = 0.1) -> dict:
        start_time = time.time()
        from sklearn.ensemble import IsolationForest
        from sklearn.preprocessing import StandardScaler

        stmt = (
            select(TransactionModel)
            .where(
                and_(
                    TransactionModel.user_id == user_id,
                    TransactionModel.deleted_at.is_(None),
                    TransactionModel.status == "completed",
                )
            )
            .order_by(TransactionModel.effective_date.asc())
        )
        result = await session.execute(stmt)
        transactions = list(result.scalars().all())

        if len(transactions) < 30:
            return {
                "samples": len(transactions),
                "error": "Need at least 30 transactions",
                "duration_seconds": 0.0,
            }

        feature_vectors = []
        for tx in transactions:
            features = extract_transaction_features(
                description=tx.description,
                amount=float(tx.amount),
                transaction_type=tx.transaction_type,
                effective_date=tx.effective_date,
                category_name=tx.category.name if tx.category else None,
                subcategory_name=tx.subcategory.name if tx.subcategory else None,
            )
            feature_vectors.append([features.get(name, 0.0) for name in TRANSACTION_FEATURE_NAMES])

        X = np.array(feature_vectors, dtype=np.float32)
        self._scaler = StandardScaler()
        X_scaled = self._scaler.fit_transform(X)

        self._model = IsolationForest(
            n_estimators=100, contamination=contamination, random_state=42, n_jobs=-1
        )
        self._model.fit(X_scaled)

        predictions = self._model.predict(X_scaled)
        scores = self._model.decision_function(X_scaled)
        n_anomalies = int(np.sum(predictions == -1))
        duration = time.time() - start_time
        self._is_trained = True
        self._threshold = float(np.percentile(scores, contamination * 100))
        self._save_model(str(user_id))

        return {
            "samples": len(transactions),
            "anomalies_detected": n_anomalies,
            "anomaly_rate": round(n_anomalies / len(transactions), 4),
            "avg_score": round(float(np.mean(scores)), 4),
            "threshold": round(self._threshold, 4),
            "duration_seconds": round(duration, 2),
        }

    async def detect(self, session: AsyncSession, user_id) -> list[dict]:
        if not self._is_trained:
            return []
        stmt = (
            select(TransactionModel)
            .where(
                and_(
                    TransactionModel.user_id == user_id,
                    TransactionModel.deleted_at.is_(None),
                    TransactionModel.status == "completed",
                )
            )
            .order_by(desc(TransactionModel.effective_date))
            .limit(50)
        )
        result = await session.execute(stmt)
        transactions = list(result.scalars().all())
        if not transactions:
            return []

        feature_vectors = []
        for tx in transactions:
            features = extract_transaction_features(
                description=tx.description,
                amount=float(tx.amount),
                transaction_type=tx.transaction_type,
                effective_date=tx.effective_date,
                category_name=tx.category.name if tx.category else None,
                subcategory_name=tx.subcategory.name if tx.subcategory else None,
            )
            feature_vectors.append([features.get(name, 0.0) for name in TRANSACTION_FEATURE_NAMES])

        X = np.array(feature_vectors, dtype=np.float32)
        X_scaled = self._scaler.transform(X)
        predictions = self._model.predict(X_scaled)
        scores = self._model.decision_function(X_scaled)

        anomalies = []
        for i, tx in enumerate(transactions):
            if predictions[i] == -1:
                score = float(scores[i])
                severity = (
                    "critical"
                    if score < -0.8
                    else "high"
                    if score < -0.6
                    else "medium"
                    if score < -0.4
                    else "low"
                )
                reasons = []
                if float(tx.amount) > 50000:
                    reasons.append(f"Monto inusualmente alto: {tx.amount}")
                reasons.append(f"Score de anomalia: {score:.2f}")
                anomalies.append(
                    {
                        "transaction_id": str(tx.id),
                        "description": tx.description,
                        "amount": str(tx.amount),
                        "transaction_type": tx.transaction_type,
                        "effective_date": tx.effective_date.isoformat(),
                        "anomaly_score": round(score, 4),
                        "severity": severity,
                        "reason": ". ".join(reasons),
                    }
                )
        anomalies.sort(key=lambda x: x["anomaly_score"])
        return anomalies

    def _save_model(self, user_id: str) -> None:
        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        path = MODEL_DIR / f"anomaly_iforest_{user_id}.joblib"
        joblib.dump(
            {
                "model": self._model,
                "scaler": self._scaler,
                "threshold": self._threshold,
                "version": self._model_version,
            },
            path,
        )
        logger.info("anomaly_detector_saved", path=str(path))

    def load_model(self, user_id: str) -> bool:
        path = MODEL_DIR / f"anomaly_iforest_{user_id}.joblib"
        if not path.exists():
            return False
        try:
            data = joblib.load(path)
            self._model = data["model"]
            self._scaler = data["scaler"]
            self._threshold = data.get("threshold", -0.5)
            self._model_version = data.get("version", "anomaly_iforest_v1.0")
            self._is_trained = True
            return True
        except Exception as e:
            logger.error("anomaly_detector_load_failed", error=str(e))
            return False


anomaly_detector = IsolationForestDetector()
