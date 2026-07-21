"""AI repository - persistence for predictions and model registry."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

import structlog
from sqlalchemy import func, select, update

from app.infrastructure.models.ai_model_registry import AIModelRegistryModel
from app.infrastructure.models.ai_prediction import AIPredictionModel

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class AIRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ==============================================================
    # Predictions CRUD
    # ==============================================================

    async def create_prediction(
        self,
        user_id: uuid.UUID,
        *,
        prediction_type: str,
        model_version: str,
        confidence: Decimal | None = None,
        predicted_value: str | None = None,
        predicted_amount: Decimal | None = None,
        reason: str | None = None,
        features_used: dict | None = None,
        metadata_json: dict | None = None,
        transaction_id: uuid.UUID | None = None,
        expires_at: datetime | None = None,
    ) -> AIPredictionModel:
        pred = AIPredictionModel(
            user_id=user_id,
            prediction_type=prediction_type,
            model_version=model_version,
            confidence=confidence,
            predicted_value=predicted_value,
            predicted_amount=predicted_amount,
            reason=reason,
            features_used=features_used,
            metadata_json=metadata_json,
            transaction_id=transaction_id,
            expires_at=expires_at,
        )
        self._session.add(pred)
        await self._session.flush()
        logger.info("ai_prediction_created", user_id=str(user_id), pred_type=prediction_type)
        return pred

    async def get_prediction(
        self, prediction_id: uuid.UUID, user_id: uuid.UUID
    ) -> AIPredictionModel | None:
        stmt = select(AIPredictionModel).where(
            AIPredictionModel.id == prediction_id,
            AIPredictionModel.user_id == user_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_predictions(
        self,
        user_id: uuid.UUID,
        *,
        prediction_type: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[AIPredictionModel], int]:
        base = select(AIPredictionModel).where(AIPredictionModel.user_id == user_id)
        if prediction_type:
            base = base.where(AIPredictionModel.prediction_type == prediction_type)
        count_stmt = select(func.count()).select_from(base.subquery())
        total = (await self._session.execute(count_stmt)).scalar() or 0
        base = base.order_by(AIPredictionModel.created_at.desc()).offset(offset).limit(limit)
        result = await self._session.execute(base)
        return list(result.scalars().all()), total

    async def delete_prediction(self, prediction_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        pred = await self.get_prediction(prediction_id, user_id)
        if pred is None:
            return False
        await self._session.delete(pred)
        await self._session.flush()
        return True

    # ==============================================================
    # Model Registry CRUD
    # ==============================================================

    async def create_model(
        self,
        user_id: uuid.UUID,
        *,
        model_type: str,
        version: str,
        display_name: str | None = None,
        hyperparameters: dict | None = None,
        feature_names: list[str] | None = None,
    ) -> AIModelRegistryModel:
        model = AIModelRegistryModel(
            user_id=user_id,
            model_type=model_type,
            version=version,
            display_name=display_name,
            status="pending",
            is_production=False,
            hyperparameters=hyperparameters,
            feature_names={"names": feature_names} if feature_names else None,
        )
        self._session.add(model)
        await self._session.flush()
        logger.info(
            "ai_model_created", user_id=str(user_id), model_type=model_type, version=version
        )
        return model

    async def get_model(
        self, model_id: uuid.UUID, user_id: uuid.UUID
    ) -> AIModelRegistryModel | None:
        stmt = select(AIModelRegistryModel).where(
            AIModelRegistryModel.id == model_id,
            AIModelRegistryModel.user_id == user_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_production_model(
        self, user_id: uuid.UUID, model_type: str
    ) -> AIModelRegistryModel | None:
        stmt = select(AIModelRegistryModel).where(
            AIModelRegistryModel.user_id == user_id,
            AIModelRegistryModel.model_type == model_type,
            AIModelRegistryModel.is_production.is_(True),
            AIModelRegistryModel.status == "completed",
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_models(
        self, user_id: uuid.UUID, *, model_type: str | None = None
    ) -> list[AIModelRegistryModel]:
        stmt = select(AIModelRegistryModel).where(AIModelRegistryModel.user_id == user_id)
        if model_type:
            stmt = stmt.where(AIModelRegistryModel.model_type == model_type)
        stmt = stmt.order_by(AIModelRegistryModel.created_at.desc())
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update_model_metrics(
        self, model_id: uuid.UUID, user_id: uuid.UUID, **kwargs
    ) -> AIModelRegistryModel | None:
        model = await self.get_model(model_id, user_id)
        if model is None:
            return None
        for key, value in kwargs.items():
            if hasattr(model, key) and value is not None:
                setattr(model, key, value)
        await self._session.flush()
        await self._session.refresh(model)
        return model

    async def promote_model(
        self, model_id: uuid.UUID, user_id: uuid.UUID
    ) -> AIModelRegistryModel | None:
        """Promote a model to production (demote others of same type)."""
        model = await self.get_model(model_id, user_id)
        if model is None:
            return None
        stmt = (
            update(AIModelRegistryModel)
            .where(
                AIModelRegistryModel.user_id == user_id,
                AIModelRegistryModel.model_type == model.model_type,
                AIModelRegistryModel.is_production.is_(True),
            )
            .values(is_production=False)
        )
        await self._session.execute(stmt)
        model.is_production = True
        await self._session.flush()
        await self._session.refresh(model)
        logger.info(
            "ai_model_promoted",
            user_id=str(user_id),
            model_type=model.model_type,
            version=model.version,
        )
        return model
