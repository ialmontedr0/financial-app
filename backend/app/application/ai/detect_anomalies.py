"""Use case: Detect anomalies in user's transactions."""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class DetectAnomaliesUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(self, user_id: uuid.UUID, *, engine: str = "isolation_forest") -> dict:
        from app.ai.anomaly.isolation_forest_detector import anomaly_detector
        from app.infrastructure.repositories.ai_repository import AIRepository

        repo = AIRepository(self._session)

        if not anomaly_detector.is_trained:
            anomaly_detector.load_model(str(user_id))

        if not anomaly_detector.is_trained:
            return {
                "anomalies": [],
                "total_checked": 0,
                "model_version": "none",
                "reason": "Model not trained. Run training first.",
            }

        anomalies = await anomaly_detector.detect(self._session, user_id)

        # Log anomalies as predictions
        for anomaly in anomalies:
            severity_map = {"low": Decimal("0.25"), "medium": Decimal("0.5"), "high": Decimal("0.75"), "critical": Decimal("1.0")}
            await repo.create_prediction(
                user_id,
                prediction_type="anomaly",
                model_version=anomaly_detector.model_version,
                confidence=severity_map.get(anomaly["severity"], Decimal("0.5")),
                predicted_value=anomaly["severity"],
                reason=anomaly["reason"],
                features_used=anomaly,
                transaction_id=uuid.UUID(anomaly["transaction_id"]),
            )

        return {
            "anomalies": anomalies,
            "total_anomalies": len(anomalies),
            "model_version": anomaly_detector.model_version,
            "reason": f"Se encontraron {len(anomalies)} anomalias en las ultimas 50 transacciones",
        }