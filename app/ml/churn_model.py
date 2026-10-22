"""Modele de scoring churn — chargement + inference."""

import pickle
import pandas as pd

from app.config import CHURN_MODEL_PATH


FEATURE_ORDER = [
    "anciennete_mois",
    "produits_detenus",
    "solde_moyen",
    "nb_interactions_90j",
    "derniere_interaction_jours",
    "age_client",
    "canal_prefere",
]

_model = None


def load_model() -> None:
    """Charge le modele XGBoost depuis le disque."""
    global _model
    try:
        with open(CHURN_MODEL_PATH, "rb") as f:
            _model = pickle.load(f)
    except FileNotFoundError:
        raise RuntimeError(
            f"Modele churn introuvable a {CHURN_MODEL_PATH}. "
            f"Lancer `python scripts/train_models.py` d'abord."
        )


def predict_churn(features: dict) -> float:
    """Predit la probabilite de churn (0.0 a 1.0) pour un client."""
    if _model is None:
        raise RuntimeError("Modele churn non charge. Appeler load_model() au startup.")
    row = {k: features[k] for k in FEATURE_ORDER}
    df = pd.DataFrame([row])
    proba = _model.predict_proba(df)[0][1]
    return float(proba)


def urgence_from_score(score: float) -> str:
    """Categorise un score en niveau d'urgence pour l'UI."""
    if score >= 0.7:
        return "high"
    elif score >= 0.4:
        return "medium"
    return "low"


if __name__ == "__main__":
    load_model()
    print("Modele charge.\n")

    client_sain = {
        "anciennete_mois": 180, "produits_detenus": 4, "solde_moyen": 25000.0,
        "nb_interactions_90j": 12, "derniere_interaction_jours": 5,
        "age_client": 52, "canal_prefere": 2,
    }
    score_sain = predict_churn(client_sain)
    print(f"Client sain  : score = {score_sain:.3f} ({urgence_from_score(score_sain)})")

    client_risque = {
        "anciennete_mois": 18, "produits_detenus": 1, "solde_moyen": 850.0,
        "nb_interactions_90j": 1, "derniere_interaction_jours": 75,
        "age_client": 28, "canal_prefere": 3,
    }
    score_risque = predict_churn(client_risque)
    print(f"Client risque: score = {score_risque:.3f} ({urgence_from_score(score_risque)})")

    print(f"\nDelta : {abs(score_risque - score_sain):.3f}")
    if score_risque > score_sain:
        print("OK - le modele distingue les deux profils.")
    else:
        print("ANOMALIE - verifier l'entrainement.")
