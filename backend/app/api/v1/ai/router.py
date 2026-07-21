"""AI endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends

from app.api.deps import get_current_active_user, get_db

router = APIRouter(prefix="/ai", tags=["AI"])


@router.post("/classify")
async def classify_transaction(
    transaction_id: uuid.UUID,
    description: str,
    category_id: uuid.UUID | None = None,
    current_user: dict = Depends(get_current_active_user),
    session=Depends(get_db),
):
    from app.application.ai.classify_transaction import ClassifyTransactionUseCase

    user_id = uuid.UUID(current_user["sub"])
    return await ClassifyTransactionUseCase(session).execute(
        user_id,
        transaction_id=transaction_id,
        description=description,
        category_id=category_id,
    )


@router.post("/classify/batch")
async def classify_batch(
    current_user: dict = Depends(get_current_active_user),
    session=Depends(get_db),
):
    from app.application.ai.classify_batch import ClassifyBatchUseCase

    user_id = uuid.UUID(current_user["sub"])
    return await ClassifyBatchUseCase(session).execute(user_id)


@router.post("/train/classifier")
async def train_classifier(
    current_user: dict = Depends(get_current_active_user),
    session=Depends(get_db),
):
    from app.application.ai.train_classifier import TrainClassifierUseCase

    user_id = uuid.UUID(current_user["sub"])
    return await TrainClassifierUseCase(session).execute(user_id)


@router.get("/classifier/status")
async def classifier_status(
    current_user: dict = Depends(get_current_active_user),
):
    from app.ai.classifiers.ml_classifier import classifier

    return {
        "is_trained": classifier.is_trained,
        "model_version": classifier.model_version,
    }


@router.post("/predict/expenses")
async def predict_expenses(
    current_user: dict = Depends(get_current_active_user),
    session=Depends(get_db),
):
    from app.application.ai.predict_expenses import PredictExpensesUseCase

    user_id = uuid.UUID(current_user["sub"])
    return await PredictExpensesUseCase(session).execute(user_id)


@router.post("/predict/income")
async def predict_income(
    current_user: dict = Depends(get_current_active_user),
    session=Depends(get_db),
):
    from app.application.ai.predict_income import PredictIncomeUseCase

    user_id = uuid.UUID(current_user["sub"])
    return await PredictIncomeUseCase(session).execute(user_id)


@router.post("/train/predictor")
async def train_predictor(
    target_type: str = "expense",
    current_user: dict = Depends(get_current_active_user),
    session=Depends(get_db),
):
    from app.application.ai.train_predictor import TrainPredictorUseCase

    user_id = uuid.UUID(current_user["sub"])
    return await TrainPredictorUseCase(session).execute(user_id, target_type=target_type)


@router.post("/anomalies/detect")
async def detect_anomalies(
    current_user: dict = Depends(get_current_active_user),
    session=Depends(get_db),
):
    from app.application.ai.detect_anomalies import DetectAnomaliesUseCase

    user_id = uuid.UUID(current_user["sub"])
    return await DetectAnomaliesUseCase(session).execute(user_id)


@router.get("/anomalies/history")
async def anomaly_history(
    limit: int = 20,
    current_user: dict = Depends(get_current_active_user),
    session=Depends(get_db),
):
    from app.infrastructure.repositories.ai_repository import AIRepository

    user_id = uuid.UUID(current_user["sub"])
    repo = AIRepository(session)
    preds, total = await repo.list_predictions(user_id, prediction_type="anomaly", limit=limit)
    return {
        "anomalies": [
            {
                "id": str(p.id),
                "predicted_value": p.predicted_value,
                "confidence": str(p.confidence) if p.confidence else None,
                "reason": p.reason,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in preds
        ],
        "total": total,
    }


@router.post("/recommendations")
async def get_recommendations(
    current_user: dict = Depends(get_current_active_user),
    session=Depends(get_db),
):
    from app.application.ai.get_recommendations import GetRecommendationsUseCase

    user_id = uuid.UUID(current_user["sub"])
    return await GetRecommendationsUseCase(session).execute(user_id)


@router.get("/recommendations/history")
async def recommendation_history(
    limit: int = 20,
    current_user: dict = Depends(get_current_active_user),
    session=Depends(get_db),
):
    from app.infrastructure.repositories.ai_repository import AIRepository

    user_id = uuid.UUID(current_user["sub"])
    repo = AIRepository(session)
    preds, total = await repo.list_predictions(
        user_id, prediction_type="recommendation", limit=limit
    )
    return {
        "recommendations": [
            {
                "id": str(p.id),
                "predicted_value": p.predicted_value,
                "reason": p.reason,
                "confidence": str(p.confidence) if p.confidence else None,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in preds
        ],
        "total": total,
    }


@router.get("/models")
async def list_models(
    model_type: str | None = None,
    current_user: dict = Depends(get_current_active_user),
    session=Depends(get_db),
):
    from app.infrastructure.repositories.ai_repository import AIRepository

    user_id = uuid.UUID(current_user["sub"])
    repo = AIRepository(session)
    models = await repo.list_models(user_id, model_type=model_type)
    return {
        "models": [
            {
                "id": str(m.id),
                "model_type": m.model_type,
                "version": m.version,
                "status": m.status,
                "is_production": m.is_production,
                "accuracy": str(m.accuracy) if m.accuracy else None,
                "training_samples": m.training_samples,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in models
        ]
    }


@router.get("/models/{model_id}")
async def get_model(
    model_id: uuid.UUID,
    current_user: dict = Depends(get_current_active_user),
    session=Depends(get_db),
):
    from app.infrastructure.repositories.ai_repository import AIRepository
    from app.middleware.error_handler import NotFoundError

    user_id = uuid.UUID(current_user["sub"])
    repo = AIRepository(session)
    model = await repo.get_model(model_id, user_id)
    if model is None:
        raise NotFoundError("AI Model")
    return {
        "id": str(model.id),
        "model_type": model.model_type,
        "version": model.version,
        "status": model.status,
        "is_production": model.is_production,
        "accuracy": str(model.accuracy) if model.accuracy else None,
        "precision_score": str(model.precision_score) if model.precision_score else None,
        "recall_score": str(model.recall_score) if model.recall_score else None,
        "f1_score": str(model.f1_score) if model.f1_score else None,
        "mse": str(model.mse) if model.mse else None,
        "mae": str(model.mae) if model.mae else None,
        "training_samples": model.training_samples,
        "hyperparameters": model.hyperparameters,
        "feature_names": model.feature_names,
        "error_message": model.error_message,
        "created_at": model.created_at.isoformat() if model.created_at else None,
    }


@router.post("/models/{model_id}/promote")
async def promote_model(
    model_id: uuid.UUID,
    current_user: dict = Depends(get_current_active_user),
    session=Depends(get_db),
):
    from app.infrastructure.repositories.ai_repository import AIRepository
    from app.middleware.error_handler import NotFoundError

    user_id = uuid.UUID(current_user["sub"])
    repo = AIRepository(session)
    model = await repo.promote_model(model_id, user_id)
    if model is None:
        raise NotFoundError("AI Model")
    return {
        "id": str(model.id),
        "model_type": model.model_type,
        "version": model.version,
        "is_production": model.is_production,
        "message": "Model promoted to production",
    }


@router.delete("/predictions/{prediction_id}")
async def delete_prediction(
    prediction_id: uuid.UUID,
    current_user: dict = Depends(get_current_active_user),
    session=Depends(get_db),
):
    from app.infrastructure.repositories.ai_repository import AIRepository
    from app.middleware.error_handler import NotFoundError

    user_id = uuid.UUID(current_user["sub"])
    repo = AIRepository(session)
    deleted = await repo.delete_prediction(prediction_id, user_id)
    if not deleted:
        raise NotFoundError("Prediction")
    return {"message": "Prediction deleted"}


# ==============================================================
# PHASE 16: Habit Analysis
# ==============================================================


@router.get("/habits/analysis")
async def habits_analysis(
    months: int = 6,
    current_user: dict = Depends(get_current_active_user),
    session=Depends(get_db),
):
    from app.application.ai.analyze_habits import AnalyzeHabitsUseCase

    user_id = uuid.UUID(current_user["sub"])
    return await AnalyzeHabitsUseCase(session).execute(user_id, months=months)


@router.get("/habits/trends")
async def habits_trends(
    months: int = 6,
    current_user: dict = Depends(get_current_active_user),
    session=Depends(get_db),
):
    from app.application.ai.get_habit_trends import GetHabitTrendsUseCase

    user_id = uuid.UUID(current_user["sub"])
    return await GetHabitTrendsUseCase(session).execute(user_id, months=months)


# ==============================================================
# PHASE 16: Risk Assessment
# ==============================================================


@router.get("/risks/assessment")
async def risks_assessment(
    current_user: dict = Depends(get_current_active_user),
    session=Depends(get_db),
):
    from app.application.ai.assess_risks import AssessRisksUseCase

    user_id = uuid.UUID(current_user["sub"])
    return await AssessRisksUseCase(session).execute(user_id)


@router.get("/risks/health-score")
async def health_score(
    current_user: dict = Depends(get_current_active_user),
    session=Depends(get_db),
):
    from app.application.ai.get_health_score import GetHealthScoreUseCase

    user_id = uuid.UUID(current_user["sub"])
    return await GetHealthScoreUseCase(session).execute(user_id)


# ==============================================================
# PHASE 16: Savings Optimization
# ==============================================================


@router.post("/savings/optimize")
async def savings_optimize(
    current_user: dict = Depends(get_current_active_user),
    session=Depends(get_db),
):
    from app.application.ai.optimize_savings import OptimizeSavingsUseCase

    user_id = uuid.UUID(current_user["sub"])
    return await OptimizeSavingsUseCase(session).execute(user_id)


@router.post("/savings/simulate")
async def savings_simulate(
    monthly_amount: float = 5000,
    months: int = 12,
    annual_return_pct: float = 0.0,
    current_user: dict = Depends(get_current_active_user),
    session=Depends(get_db),
):
    from app.application.ai.simulate_savings import SimulateSavingsUseCase

    user_id = uuid.UUID(current_user["sub"])
    return await SimulateSavingsUseCase(session).execute(
        user_id,
        monthly_amount=monthly_amount,
        months=months,
        annual_return_pct=annual_return_pct,
    )


# ==============================================================
# PHASE 16: Personalized Explanations
# ==============================================================


@router.post("/explain")
async def explain_recommendation(
    rec_type: str,
    title: str = "",
    description: str = "",
    priority: str = "medium",
    estimated_savings: float = 0,
    confidence: float = 0.5,
    current_user: dict = Depends(get_current_active_user),
    session=Depends(get_db),
):
    from app.application.ai.get_personalized_explanation import (
        GetPersonalizedExplanationUseCase,
    )

    user_id = uuid.UUID(current_user["sub"])
    recommendation = {
        "type": rec_type,
        "title": title,
        "description": description,
        "priority": priority,
        "estimated_savings": estimated_savings,
        "confidence": confidence,
        "features_used": {},
    }
    return await GetPersonalizedExplanationUseCase(session).execute(user_id, recommendation)


# ==============================================================
# PHASE 16: Dashboard
# ==============================================================


@router.get("/dashboard")
async def dashboard(
    current_user: dict = Depends(get_current_active_user),
    session=Depends(get_db),
):
    from app.application.ai.get_dashboard import GetDashboardUseCase

    user_id = uuid.UUID(current_user["sub"])
    return await GetDashboardUseCase(session).execute(user_id)
