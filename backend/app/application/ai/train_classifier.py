"""Use case: Train the transaction classifier."""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class TrainClassifierUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(self, user_id: uuid.UUID) -> dict:
        """Train the classifier on the user's categorized transactions.

        Fetches all transactions with a category assigned, uses them
        as training data for TF-IDF + LinearSVC.
        """
        from sqlalchemy import and_, select

        from app.ai.classifiers.ml_classifier import classifier
        from app.infrastructure.models.category import CategoryModel
        from app.infrastructure.models.transaction import TransactionModel
        from app.infrastructure.repositories.ai_repository import AIRepository

        repo = AIRepository(self._session)

        # Fetch categorized transactions
        stmt = (
            select(TransactionModel.description, CategoryModel.name)
            .join(CategoryModel, TransactionModel.category_id == CategoryModel.id)
            .where(
                and_(
                    TransactionModel.user_id == user_id,
                    TransactionModel.deleted_at.is_(None),
                    TransactionModel.status == "completed",
                    TransactionModel.transaction_type.in_(["expense", "income"]),
                    TransactionModel.category_id.isnot(None),
                )
            )
        )
        result = await self._session.execute(stmt)
        rows = result.all()

        if len(rows) < 50:
            return {
                "success": False,
                "samples": len(rows),
                "error": f"Need at least 50 categorized transactions. Found {len(rows)}.",
            }

        training_data = [(desc, cat_name) for desc, cat_name in rows]

        # Train
        metrics = await classifier.train(training_data, user_id=str(user_id))

        # Register in model registry
        model = await repo.create_model(
            user_id,
            model_type="classifier_tfidf_lsvc",
            version=classifier.model_version,
            display_name=f"TF-IDF+LinearSVC Classifier v{classifier.model_version}",
            hyperparameters={"max_features": 5000, "ngram_range": [1, 2], "C": 1.0},
            feature_names=["description_text"],
        )

        report = metrics.get("report", {})
        await repo.update_model_metrics(
            model.id,
            user_id,
            status="completed",
            accuracy=Decimal(str(metrics.get("accuracy", 0))),
            precision_score=Decimal(str(report.get("precision", 0))),
            recall_score=Decimal(str(report.get("recall", 0))),
            f1_score=Decimal(str(report.get("f1", 0))),
            training_samples=metrics.get("samples", 0),
            training_duration_seconds=Decimal(str(metrics.get("duration_seconds", 0))),
        )

        # Log a training prediction
        await repo.create_prediction(
            user_id,
            prediction_type="classification",
            model_version=classifier.model_version,
            confidence=Decimal(str(metrics.get("accuracy", 0))),
            reason=f"Classifier trained: accuracy={metrics.get('accuracy', 0):.2%}, "
            f"samples={metrics.get('samples', 0)}, "
            f"categories={metrics.get('categories', 0)}",
            features_used={"training_metrics": metrics},
        )

        logger.info("classifier_training_completed", user_id=str(user_id), metrics=metrics)

        return {
            "success": True,
            "model_id": str(model.id),
            "model_version": classifier.model_version,
            **metrics,
        }
