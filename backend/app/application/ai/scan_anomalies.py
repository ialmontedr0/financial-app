"""Use Case: Corre deteccion de anomalias para todos los usuarios."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.user_repository import UserRepository

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class ScanAnomaliesUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._user_repo = UserRepository(session)

    async def execute(self) -> dict:
        from app.application.ai.detect_anomalies import DetectAnomaliesUseCase

        user_ids = await self._user_repo.list_active_ids()
        results: list[dict] = []
        total = 0

        for user_id in user_ids:
            try:
                res = await DetectAnomaliesUseCase(self._session).execute(user_id)
                total += len(res.get("anomalies", []))
                results.append(
                    {"user_id": str(user_id), "anomalies": len(res.get("anomalies", []))}
                )
            except Exception as exc:
                logger.error("anomaly_scan_user_failed", user_id=str(user_id), error=str(exc))
                results.append({"user_id": str(user_id), "anomalies": 0, "error": str(exc)})

        logger.info("anomalies_scanned", users=len(user_ids), total=total)
        return {"users_scanned": len(user_ids), "total_anomalies": total, "results": results}
