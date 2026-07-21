"""ML-based transaction classifier using TF-IDF + LinearSVC."""

from __future__ import annotations

import math
import os  # noqa: F401
import re
import time
from pathlib import Path

import joblib
import structlog

logger = structlog.get_logger()
MODEL_DIR = Path("backend/ai_models")


class TransactionClassifier:
    def __init__(self) -> None:
        self._vectorizer = None
        self._classifier = None
        self._is_trained = False
        self._model_version = "classifier_v1.0"

    @property
    def is_trained(self) -> bool:
        return self._is_trained

    @property
    def model_version(self) -> str:
        return self._model_version

    @staticmethod
    def _preprocess(text: str) -> str:
        text = text.lower().strip()
        text = re.sub(r"[^\w\s]", " ", text)
        return re.sub(r"\s+", " ", text)

    async def predict(self, description: str, merchant_name: str | None = None) -> dict | None:
        if not self._is_trained:
            return None
        from sklearn.feature_extraction.text import TfidfVectorizer  # noqa: F401

        text = merchant_name or description
        processed = self._preprocess(text)
        features = self._vectorizer.transform([processed])
        prediction = self._classifier.predict(features)[0]
        decision = self._classifier.decision_function(features)
        if hasattr(decision, "shape") and len(decision.shape) > 1:
            confidence = float(max(decision[0]))
        else:
            confidence = float(max(decision[0])) if len(decision) > 0 else 0.0
        confidence_normalized = 1.0 / (1.0 + math.exp(-confidence))
        confidence_normalized = min(max(confidence_normalized, 0.0), 1.0)
        return {
            "category_slug": str(prediction),
            "confidence": round(confidence_normalized, 4),
            "model_version": self._model_version,
            "features_used": processed.split()[:10],
        }

    async def train(self, training_data: list[tuple[str, str]], user_id: str | None = None) -> dict:
        start_time = time.time()
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics import accuracy_score, classification_report
        from sklearn.model_selection import train_test_split
        from sklearn.svm import LinearSVC

        texts = [self._preprocess(t) for t, _ in training_data]
        labels = [c for _, c in training_data]
        unique_labels = set(labels)
        if len(unique_labels) < 2:
            return {
                "accuracy": 0.0,
                "samples": len(training_data),
                "categories": len(unique_labels),
                "error": "Need at least 2 categories",
                "duration_seconds": 0.0,
            }
        X_train, X_test, y_train, y_test = train_test_split(
            texts, labels, test_size=0.2, random_state=42
        )
        self._vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1, 2), sublinear_tf=True)
        X_train_tfidf = self._vectorizer.fit_transform(X_train)
        X_test_tfidf = self._vectorizer.transform(X_test)
        self._classifier = LinearSVC(max_iter=2000, C=1.0, class_weight="balanced")
        self._classifier.fit(X_train_tfidf, y_train)
        y_pred = self._classifier.predict(X_test_tfidf)
        accuracy = float(accuracy_score(y_test, y_pred))
        report = classification_report(y_test, y_pred, output_dict=True, zero_division=0)
        duration = time.time() - start_time
        self._is_trained = True
        if user_id:
            self._save_model(user_id)
        return {
            "accuracy": round(accuracy, 4),
            "samples": len(training_data),
            "categories": len(unique_labels),
            "duration_seconds": round(duration, 2),
            "report": {
                "precision": round(report.get("weighted avg", {}).get("precision", 0), 4),
                "recall": round(report.get("weighted avg", {}).get("recall", 0), 4),
                "f1": round(report.get("weighted avg", {}).get("f1-score", 0), 4),
            },
        }

    def _save_model(self, user_id: str) -> None:
        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        path = MODEL_DIR / f"classifier_{user_id}.joblib"
        joblib.dump(
            {
                "vectorizer": self._vectorizer,
                "classifier": self._classifier,
                "version": self._model_version,
            },
            path,
        )
        logger.info("classifier_saved", path=str(path))

    def load_model(self, user_id: str) -> bool:
        path = MODEL_DIR / f"classifier_{user_id}.joblib"
        if not path.exists():
            return False
        try:
            data = joblib.load(path)
            self._vectorizer = data["vectorizer"]
            self._classifier = data["classifier"]
            self._model_version = data.get("version", "classifier_v1.0")
            self._is_trained = True
            return True
        except Exception as e:
            logger.error("classifier_load_failed", error=str(e))
            return False


classifier = TransactionClassifier()
