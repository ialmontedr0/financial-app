"""ML-based transaction classifier using TF-IDF + LinearSVC.

This is a SKELETON. The actual training will happen in Phase 15
when transaction data is available.

Free stack: scikit-learn (already in dependencies).
"""

from __future__ import annotations

import re

import structlog

logger = structlog.get_logger()


class TransactionClassifier:
    """ML classifier for transaction categorization.

    Uses TF-IDF vectorization + LinearSVC for fast inference.
    Trained on (description, category) pairs.

    Inference time: < 1ms per transaction.
    """

    def __init__(self) -> None:
        self._vectorizer = None
        self._classifier = None
        self._is_trained = False

    @staticmethod
    def _preprocess(text: str) -> str:
        """Clean and normalize transaction text."""
        text = text.lower().strip()
        text = re.sub(r"[^\w\s]", " ", text)
        text = re.sub(r"\s+", " ", text)
        return text

    async def predict(
        self,
        description: str,
        merchant_name: str | None = None,
    ) -> dict | None:
        """
        Predict category for a transaction.

        Returns:
            {
                "category_slug": "food",
                "subcategory_slug": "groceries",
                "confidence": 0.92,
                "model_version": "v1.0",
                "features_used": ["walmart", "supercenter"],
            }
            or None if not trained.
        """
        if not self._is_trained:
            return None

        text = merchant_name or description
        self._preprocess(text)

        # TODO: Phase 15 — implement actual prediction
        # from sklearn.feature_extraction.text import TfidfVectorizer
        # from sklearn.svm import LinearSVC
        #
        # features = self._vectorizer.transform([processed])
        # prediction = self._classifier.predict(features)[0]
        # confidence = max(self._classifier.decision_function(features)[0])
        #
        # return {
        #     "category_slug": prediction,
        #     "confidence": float(confidence),
        #     "model_version": "v1.0",
        #     "features_used": processed.split(),
        # }

        return None

    async def train(
        self,
        training_data: list[tuple[str, str]],
    ) -> dict:
        """
        Train the classifier on (text, category_slug) pairs.

        Args:
            training_data: List of (description, category_slug) tuples

        Returns:
            Training metrics: {accuracy, samples, categories}
        """
        # TODO: Phase 15 — implement actual training
        #
        # from sklearn.feature_extraction.text import TfidfVectorizer
        # from sklearn.svm import LinearSVC
        # from sklearn.model_selection import train_test_split
        # from sklearn.metrics import accuracy_score
        #
        # texts = [self._preprocess(t) for t, _ in training_data]
        # labels = [c for _, c in training_data]
        #
        # X_train, X_test, y_train, y_test = train_test_split(
        #     texts, labels, test_size=0.2, random_state=42
        # )
        #
        # self._vectorizer = TfidfVectorizer(
        #     max_features=5000,
        #     ngram_range=(1, 2),
        #     analyzer="word",
        # )
        # X_train_tfidf = self._vectorizer.fit_transform(X_train)
        # X_test_tfidf = self._vectorizer.transform(X_test)
        #
        # self._classifier = LinearSVC(max_iter=1000)
        # self._classifier.fit(X_train_tfidf, y_train)
        #
        # accuracy = accuracy_score(y_test, self._classifier.predict(X_test_tfidf))
        # self._is_trained = True
        #
        # return {
        #     "accuracy": float(accuracy),
        #     "samples": len(training_data),
        #     "categories": len(set(labels)),
        # }

        logger.info("ml_classifier_train_not_implemented_yet")
        return {"accuracy": 0.0, "samples": 0, "categories": 0, "note": "Phase 15"}


# Singleton
classifier = TransactionClassifier()
