from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

PREDICTION_TYPES: dict[str, str] = {
    "expense_forecast": "Prediccion de Gastos",
    "income_forecast": "Prediccion de Ingresos",
    "anomaly": "Anomalia Detectada",
    "classification": "Clasificacion de Transaccion",
    "recommendation": "Recomendacion Financiera",
    "goal_forecast": "Prediccion de Meta",
}


@dataclass(frozen=True)
class PredictionType:
    value: str
    _VALID_TYPES: ClassVar[frozenset[str]] = frozenset(PREDICTION_TYPES.keys())

    def __post_init__(self) -> None:
        normalized = self.value.lower().strip()
        if normalized not in self._VALID_TYPES:
            supported = ", ".join(sorted(self._VALID_TYPES))
            raise ValueError(
                f"Tipo de prediccion no soportado: {self.value}. Soportado: {supported}"
            )
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value

    @property
    def name(self) -> str:
        return PREDICTION_TYPES.get(self.value, self.value)


MODEL_TYPES: dict[str, str] = {
    "classifier_tfidf_lsvc": "TF-IDF + LinearSVC Classifier",
    "expense_predictor_xgboost": "XGBoost Expense Predictor",
    "income_predictor_xgboost": "XGBoost Income Predictor",
    "anomaly_isolation_forest": "Isolation Forest Anomaly Detector",
    "anomaly_autoencoder": "PyTorch Autoencoder Anomaly Detector",
    "lstm_predictor": "LSTM Sequence Predictor",
    "gru_predictor": "GRU Sequence Predictor",
    "nbeats_predictor": "N-BEATS Forecasting Model",
    "tft_predictor": "Temporal Fusion Transformer",
    "embedding_model": "Transaction Embedding Model",
    "bert_classifier": "BERT-based Text Classifier",
    "xgboost_ensemble": "XGBoost Ensemble Model",
}


@dataclass(frozen=True)
class ModelType:
    value: str
    _VALID_TYPES: ClassVar[frozenset[str]] = frozenset(MODEL_TYPES.keys())

    def __post_init__(self) -> None:
        normalized = self.value.lower().strip()
        if normalized not in self._VALID_TYPES:
            supported = ", ".join(sorted(self._VALID_TYPES))
            raise ValueError(f"Tipo de modelo no soportado: {self.value}. Soportado: {supported}")
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value

    @property
    def name(self) -> str:
        return MODEL_TYPES.get(self.value, self.value)


ANOMALY_SEVERITIES: dict[str, str] = {
    "low": "Baja",
    "medium": "Media",
    "high": "Alta",
    "critical": "Critica",
}


@dataclass(frozen=True)
class AnomalySeverity:
    value: str
    _VALID_TYPES: ClassVar[frozenset[str]] = frozenset(ANOMALY_SEVERITIES.keys())

    def __post_init__(self) -> None:
        normalized = self.value.lower().strip()
        if normalized not in self._VALID_TYPES:
            supported = ", ".join(sorted(self._VALID_TYPES))
            raise ValueError(f"Severidad no soportada: {self.value}. Soportado: {supported}")
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value

    @property
    def name(self) -> str:
        return ANOMALY_SEVERITIES.get(self.value, self.value)


RECOMMENDATION_TYPES: dict[str, str] = {
    "reduce_spending": "Reducir Gasto",
    "increase_savings": "Aumentar Ahorro",
    "cancel_subscription": "Cancelar Suscripcion",
    "switch_plan": "Cambiar de Plan",
    "pay_debt": "Pagar Deuda",
    "build_emergency_fund": "Construir Fondo de Emergencia",
    "optimize_categories": "Optimizar Categorias",
    "budget_adjustment": "Ajuste de Presupuesto",
    "habit_optimization": "Optimizar Habito",
    "spending_pattern": "Patron de Gasto",
    "income_volatility": "Volatilidad de Ingreso",
    "debt_risk": "Riesgo de Deuda",
    "subscription_creep": "Aumento de Suscripciones",
    "savings_allocation": "Asignacion de Ahorro",
    "debt_strategy": "Estrategia de Deuda",
    "seasonal_saving": "Ahorro Estacional",
    "financial_health": "Salud Financiera",
}


@dataclass(frozen=True)
class RecommendationType:
    value: str
    _VALID_TYPES: ClassVar[frozenset[str]] = frozenset(RECOMMENDATION_TYPES.keys())

    def __post_init__(self) -> None:
        normalized = self.value.lower().strip()
        if normalized not in self._VALID_TYPES:
            supported = ", ".join(sorted(self._VALID_TYPES))
            raise ValueError(
                f"Tipo de recomendacion no soportado: {self.value}. Soportado: {supported}"
            )
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value

    @property
    def name(self) -> str:
        return RECOMMENDATION_TYPES.get(self.value, self.value)


TRAINING_STATUSES: dict[str, str] = {
    "pending": "Pendiente",
    "training": "Entrenando",
    "completed": "Completado",
    "failed": "Fallido",
    "deprecated": "Deprecado",
}


@dataclass(frozen=True)
class TrainingStatus:
    value: str
    _VALID_TYPES: ClassVar[frozenset[str]] = frozenset(TRAINING_STATUSES.keys())

    def __post_init__(self) -> None:
        normalized = self.value.lower().strip()
        if normalized not in self._VALID_TYPES:
            supported = ", ".join(sorted(self._VALID_TYPES))
            raise ValueError(
                f"Estado de entrenamiento no soportado: {self.value}. Soportado: {supported}"
            )
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value

    @property
    def name(self) -> str:
        return TRAINING_STATUSES.get(self.value, self.value)


RISK_LEVELS: dict[str, str] = {
    "low": "Bajo",
    "medium": "Medio",
    "high": "Alto",
    "critical": "Critico",
}


@dataclass(frozen=True)
class RiskLevel:
    value: str
    _VALID_TYPES: ClassVar[frozenset[str]] = frozenset(RISK_LEVELS.keys())

    def __post_init__(self) -> None:
        normalized = self.value.lower().strip()
        if normalized not in self._VALID_TYPES:
            supported = ", ".join(sorted(self._VALID_TYPES))
            raise ValueError(f"Nivel de riesgo no soportado: {self.value}. Soportado: {supported}")
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value

    @property
    def name(self) -> str:
        return RISK_LEVELS.get(self.value, self.value)


HABIT_TYPES: dict[str, str] = {
    "spending_frequency": "Frecuencia de Gasto",
    "spending_amount": "Monto de Gasto",
    "income_regularity": "Regularidad de Ingreso",
    "category_dominance": "Dominancia de Categoria",
    "weekend_spending": "Gasto de Fin de Semana",
    "payday_spending": "Gasto de Dia de Pago",
}


@dataclass(frozen=True)
class HabitType:
    value: str
    _VALID_TYPES: ClassVar[frozenset[str]] = frozenset(HABIT_TYPES.keys())

    def __post_init__(self) -> None:
        normalized = self.value.lower().strip()
        if normalized not in self._VALID_TYPES:
            supported = ", ".join(sorted(self._VALID_TYPES))
            raise ValueError(f"Tipo de habito no soportado: {self.value}. Soportado: {supported}")
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value

    @property
    def name(self) -> str:
        return HABIT_TYPES.get(self.value, self.value)


OPTIMIZATION_STRATEGIES: dict[str, str] = {
    "50_30_20": "Regla 50/30/20",
    "debt_snowball": "Bola de Nieve (Deudas)",
    "debt_avalanche": "Avalancha (Deudas)",
    "goal_first": "Metas Primero",
    "emergency_first": "Emergencia Primero",
    "balanced": "Equilibrado",
}


@dataclass(frozen=True)
class OptimizationStrategy:
    value: str
    _VALID_TYPES: ClassVar[frozenset[str]] = frozenset(OPTIMIZATION_STRATEGIES.keys())

    def __post_init__(self) -> None:
        normalized = self.value.lower().strip()
        if normalized not in self._VALID_TYPES:
            supported = ", ".join(sorted(self._VALID_TYPES))
            raise ValueError(f"Estrategia no soportada: {self.value}. Soportado: {supported}")
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value

    @property
    def name(self) -> str:
        return OPTIMIZATION_STRATEGIES.get(self.value, self.value)
