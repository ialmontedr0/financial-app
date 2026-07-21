"""Anomaly detection using PyTorch Autoencoder."""

from __future__ import annotations

import time
from pathlib import Path

import joblib
import numpy as np
import structlog
import torch
import torch.nn as nn
from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.features.feature_extractor import (
    TRANSACTION_FEATURE_NAMES,
    extract_transaction_features,
)
from app.infrastructure.models.transaction import TransactionModel

logger = structlog.get_logger()
MODEL_DIR = Path("backend/ai_models")
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


class TransactionAutoencoder(nn.Module):
    def __init__(self, input_dim: int = 22, hidden_dim: int = 16, latent_dim: int = 8):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.BatchNorm1d(hidden_dim),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim, latent_dim),
            nn.ReLU(),
        )
        self.decoder = nn.Sequential(
            nn.Linear(latent_dim, hidden_dim),
            nn.ReLU(),
            nn.BatchNorm1d(hidden_dim),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim, input_dim),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.decoder(self.encoder(x))

    def get_reconstruction_error(self, x: torch.Tensor) -> torch.Tensor:
        return torch.mean((x - self.forward(x)) ** 2, dim=1)


class AutoencoderDetector:
    def __init__(self) -> None:
        self._model: TransactionAutoencoder | None = None
        self._scaler = None
        self._is_trained = False
        self._model_version = "anomaly_autoencoder_v1.0"
        self._threshold: float = 0.0
        self._input_dim: int = len(TRANSACTION_FEATURE_NAMES)

    @property
    def is_trained(self) -> bool:
        return self._is_trained

    @property
    def model_version(self) -> str:
        return self._model_version

    async def train(
        self,
        session: AsyncSession,
        user_id,
        *,
        epochs: int = 100,
        learning_rate: float = 0.001,
        threshold_percentile: float = 95.0,
    ) -> dict:
        start_time = time.time()
        from sklearn.preprocessing import StandardScaler

        stmt = (
            select(TransactionModel)
            .where(
                and_(
                    TransactionModel.user_id == user_id,
                    TransactionModel.deleted_at.is_(None),
                    TransactionModel.status == "completed",
                )
            )
            .order_by(TransactionModel.effective_date.asc())
        )
        result = await session.execute(stmt)
        transactions = list(result.scalars().all())

        if len(transactions) < 50:
            return {
                "samples": len(transactions),
                "error": "Need at least 50 transactions",
                "duration_seconds": 0.0,
            }

        feature_vectors = []
        for tx in transactions:
            features = extract_transaction_features(
                description=tx.description,
                amount=float(tx.amount),
                transaction_type=tx.transaction_type,
                effective_date=tx.effective_date,
                category_name=tx.category.name if tx.category else None,
                subcategory_name=tx.subcategory.name if tx.subcategory else None,
            )
            feature_vectors.append([features.get(name, 0.0) for name in TRANSACTION_FEATURE_NAMES])

        X = np.array(feature_vectors, dtype=np.float32)
        self._scaler = StandardScaler()
        X_scaled = self._scaler.fit_transform(X)
        X_tensor = torch.FloatTensor(X_scaled).to(DEVICE)

        self._model = TransactionAutoencoder(input_dim=self._input_dim).to(DEVICE)
        optimizer = torch.optim.Adam(self._model.parameters(), lr=learning_rate)
        criterion = nn.MSELoss(reduction="none")

        self._model.train()
        batch_size = min(32, len(X_scaled))
        for _ in range(epochs):
            perm = torch.randperm(len(X_tensor))
            for i in range(0, len(X_tensor), batch_size):
                batch = X_tensor[perm[i : i + batch_size]]
                optimizer.zero_grad()
                loss = criterion(self._model(batch), batch).mean()
                loss.backward()
                optimizer.step()

        self._model.eval()
        with torch.no_grad():
            errors = self._model.get_reconstruction_error(X_tensor).cpu().numpy()
        self._threshold = float(np.percentile(errors, threshold_percentile))
        duration = time.time() - start_time
        self._is_trained = True
        self._save_model(str(user_id))

        return {
            "samples": len(transactions),
            "epochs": epochs,
            "avg_reconstruction_error": round(float(np.mean(errors)), 6),
            "threshold": round(self._threshold, 6),
            "duration_seconds": round(duration, 2),
        }

    async def detect(self, session: AsyncSession, user_id) -> list[dict]:
        if not self._is_trained:
            return []
        stmt = (
            select(TransactionModel)
            .where(
                and_(
                    TransactionModel.user_id == user_id,
                    TransactionModel.deleted_at.is_(None),
                    TransactionModel.status == "completed",
                )
            )
            .order_by(desc(TransactionModel.effective_date))
            .limit(50)
        )
        result = await session.execute(stmt)
        transactions = list(result.scalars().all())
        if not transactions:
            return []

        feature_vectors = []
        for tx in transactions:
            features = extract_transaction_features(
                description=tx.description,
                amount=float(tx.amount),
                transaction_type=tx.transaction_type,
                effective_date=tx.effective_date,
                category_name=tx.category.name if tx.category else None,
                subcategory_name=tx.subcategory.name if tx.subcategory else None,
            )
            feature_vectors.append([features.get(name, 0.0) for name in TRANSACTION_FEATURE_NAMES])

        X = np.array(feature_vectors, dtype=np.float32)
        X_scaled = self._scaler.transform(X)
        X_tensor = torch.FloatTensor(X_scaled).to(DEVICE)

        self._model.eval()
        with torch.no_grad():
            errors = self._model.get_reconstruction_error(X_tensor).cpu().numpy()

        anomalies = []
        for i, tx in enumerate(transactions):
            error = float(errors[i])
            if error > self._threshold:
                severity = (
                    "critical"
                    if error > self._threshold * 3
                    else "high"
                    if error > self._threshold * 2
                    else "medium"
                    if error > self._threshold * 1.5
                    else "low"
                )
                anomalies.append(
                    {
                        "transaction_id": str(tx.id),
                        "description": tx.description,
                        "amount": str(tx.amount),
                        "transaction_type": tx.transaction_type,
                        "effective_date": tx.effective_date.isoformat(),
                        "anomaly_score": round(error, 6),
                        "severity": severity,
                        "reason": f"Error de reconstruccion: {error:.4f} (umbral: {self._threshold:.4f})",
                    }
                )
        anomalies.sort(key=lambda x: x["anomaly_score"], reverse=True)
        return anomalies

    def _save_model(self, user_id: str) -> None:
        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        path = MODEL_DIR / f"anomaly_autoencoder_{user_id}.pt"
        torch.save(
            {
                "model_state_dict": self._model.state_dict(),
                "input_dim": self._input_dim,
                "threshold": self._threshold,
                "version": self._model_version,
            },
            path,
        )
        scaler_path = MODEL_DIR / f"anomaly_autoencoder_scaler_{user_id}.joblib"
        joblib.dump(self._scaler, scaler_path)
        logger.info("autoencoder_saved", path=str(path))

    def load_model(self, user_id: str) -> bool:
        path = MODEL_DIR / f"anomaly_autoencoder_{user_id}.pt"
        scaler_path = MODEL_DIR / f"anomaly_autoencoder_scaler_{user_id}.joblib"
        if not path.exists() or not scaler_path.exists():
            return False
        try:
            checkpoint = torch.load(path, map_location=DEVICE, weights_only=True)
            self._model = TransactionAutoencoder(input_dim=checkpoint["input_dim"]).to(DEVICE)
            self._model.load_state_dict(checkpoint["model_state_dict"])
            self._model.eval()
            self._scaler = joblib.load(scaler_path)
            self._threshold = checkpoint.get("threshold", 0.0)
            self._model_version = checkpoint.get("version", "anomaly_autoencoder_v1.0")
            self._input_dim = checkpoint.get("input_dim", len(TRANSACTION_FEATURE_NAMES))
            self._is_trained = True
            return True
        except Exception as e:
            logger.error("autoencoder_load_failed", error=str(e))
            return False


autoencoder_detector = AutoencoderDetector()
