"""SHAP explainer — extraction des top features contribuant au score."""

import pickle
from typing import Optional

from app.config import SHAP_EXPLAINER_PATH


_explainer: Optional[object] = None  # shap.TreeExplainer


def load_explainer() -> None:
    """Charge le SHAP explainer depuis le disque."""
    global _explainer
    # TODO : with open(SHAP_EXPLAINER_PATH, "rb") as f: _explainer = pickle.load(f)
    pass


def get_top_features(client_features: dict, top_n: int = 5) -> list[dict]:
    """Retourne les N features les plus contributrices au score churn.

    Args:
        client_features: features du client.
        top_n: nombre de features à retourner.

    Returns:
        Liste de dicts : [{"feature": str, "value": float, "shap_value": float, "direction": "+/-"}, ...]
    """
    # TODO : _explainer.shap_values(X)
    # TODO : trier par |shap_value| décroissant
    # TODO : retourner top_n avec le signe (positif = pousse vers churn)
    raise NotImplementedError("À implémenter en phase 4")
