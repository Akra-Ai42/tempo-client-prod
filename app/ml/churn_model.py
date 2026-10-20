"""Modèle de scoring churn — XGBoost.

Chargé une seule fois au démarrage via le lifespan de FastAPI.
Inférence synchrone via `predict_churn(features)`.
"""

import pickle
from typing import Optional

from app.config import CHURN_MODEL_PATH


_model: Optional[object] = None  # XGBClassifier chargé


def load_model() -> None:
    """Charge le modèle depuis le disque (appelé au startup FastAPI)."""
    global _model
    # TODO : with open(CHURN_MODEL_PATH, "rb") as f: _model = pickle.load(f)
    pass


def predict_churn(features: dict) -> float:
    """Retourne la probabilité de churn (0.0 à 1.0) pour un client.

    Args:
        features: dict des features du client (anciennete, produits, solde, etc.)

    Returns:
        Probabilité de churn entre 0.0 et 1.0.
    """
    # TODO : vérifier que _model est chargé
    # TODO : convertir features en DataFrame/array dans le bon ordre
    # TODO : _model.predict_proba(X)[0][1]
    raise NotImplementedError("À implémenter en phase 4")


def urgence_from_score(score: float) -> str:
    """Catégorise un score en urgence (low / medium / high)."""
    if score >= 0.7:
        return "high"
    elif score >= 0.4:
        return "medium"
    return "low"
