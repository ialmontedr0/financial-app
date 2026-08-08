"""Helper de anomalias de notificaciones."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()

_NOTIFIABLE_SEVERITIES = {"medium", "high", "critical"}


async def emit_anomaly_notifications(
    session: AsyncSession, user_id: uuid.UUID, anomalies: list[dict]
) -> int:
    """Envia una notificacion in-app 'anomaly_detected' por anomalia notificable."""
    from app.notifications.service import NotificationService

    service = NotificationService(session)
    emitted = 0

    for anomaly in anomalies:
        severity = str(anomaly.get("severity", "low"))
        if severity not in _NOTIFIABLE_SEVERITIES:
            continue

        transaction_id = anomaly.get("transaction_id")
        if transaction_id:
            # Dedup entre ejecuciones: no volver a notificar la misma anomalía
            # (transaction_id) que ya fue emitida.
            from app.infrastructure.repositories.notification_repository import (
                NotificationRepository,
            )

            already = await NotificationRepository(session).exists_with_data(
                user_id, "anomaly_detected", "transaction_id", str(transaction_id)
            )
            if already:
                continue

        data: dict = {
            "severity": severity,
            "anomaly_score": anomaly.get("anomaly_score"),
            "reason": anomaly.get("reason"),
            "transaction_id": str(transaction_id) if transaction_id else None,
        }
        if transaction_id:
            data["link"] = f"/transactions/{transaction_id}"

        await service.send(
            user_id=user_id,
            type="anomaly_detected",
            title=f"Anomalia {severity} detectada",
            body=(
                f"Se detecto actividad {severity} en tu cuenta. "
                f"{anomaly.get('reason') or 'Revisa el detalle de la transaccion.'}"
            ),
            data=data,
        )
        emitted += 1

    if emitted:
        logger.info("anomaly_notifications", user_id=str(user_id), emitted=emitted)
    return emitted
