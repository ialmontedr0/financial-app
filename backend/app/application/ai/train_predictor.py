"""Use case: Train the expense/income predictor."""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class TrainPredictorUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(
        self,
        user_id: uuid.UUID,
        *,
        target_type: str = "expense",
    ) -> dict:
        """Train the XGBoost expense/income predictor."""
        from app.ai.predictors.expense_predictor import ExpensePredictor
        from app.infrastructure.repositories.ai_repository import AIRepository

        repo = AIRepository(self._session)
        predictor = ExpensePredictor()
        predictor._target_type = target_type
        if target_type == "income":
            predictor._model_version = "xgb_income_v1.0"
        else:
            predictor._model_version = "xgb_expense_v1.0"

        # Train
        metrics = await predictor.train(
            self._session,
            user_id,
            target_type=target_type,
        )

        if "error" in metrics:
            return {"success": False, **metrics}

        # Register in model registry
        model_type = f"{target_type}_predictor_xgboost"
        model = await repo.create_model(
            user_id,
            model_type=model_type,
            version=predictor._model_version,
            display_name=f"XGBoost {target_type.title()} Predictor v{predictor._model_version}",
            hyperparameters={
                "n_estimators": 100,
                "max_depth": 4,
                "learning_rate": 0.1,
                "objective": "reg:squarederror",
            },
            feature_names=[
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
            ],
        )

        await repo.update_model_metrics(
            model.id,
            user_id,
            status="completed",
            r2=Decimal(str(metrics.get("r2", 0))),
            mse=Decimal(str(metrics.get("mse", 0))),
            mae=Decimal(str(metrics.get("mae", 0))),
            training_samples=metrics.get("samples", 0),
            training_duration_seconds=Decimal(str(metrics.get("duration_seconds", 0))),
        )

        # Log training event
        await repo.create_prediction(
            user_id,
            prediction_type=f"{target_type}_forecast",
            model_version=predictor._model_version,
            reason=(
                f"Predictor trained: r2={metrics.get('r2', 0):.4f}, "
                f"samples={metrics.get('samples', 0)}, "
                f"months={metrics.get('months_used', 0)}"
            ),
            features_used={"training_metrics": metrics},
        )

        logger.info(
            "predictor_training_completed",
            user_id=str(user_id),
            target_type=target_type,
            metrics=metrics,
        )

        return {
            "success": True,
            "model_id": str(model.id),
            "model_version": predictor._model_version,
            "target_type": target_type,
            **metrics,
        }
