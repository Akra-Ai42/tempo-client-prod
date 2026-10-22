"""SHAP explainer — extraction des features les plus contributrices."""

import pickle
import pandas as pd

from app.config import SHAP_EXPLAINER_PATH
from app.ml.churn_model import FEATURE_ORDER


_explainer = None


def load_explainer() -> None:
    """Charge le SHAP TreeExplainer depuis le disque."""
    global _explainer
    try:
        with open(SHAP_EXPLAINER_PATH, "rb") as f:
            _explainer = pickle.load(f)
    except FileNotFoundError:
        raise RuntimeError(
            f"SHAP explainer introuvable a {SHAP_EXPLAINER_PATH}. "
            f"Lancer `python scripts/train_models.py` d'abord."
        )


def get_top_features(client_features: dict, top_n: int = 5) -> list[dict]:
    """Retourne les N features les plus contributrices au score churn."""
    if _explainer is None:
        raise RuntimeError("SHAP explainer non charge. Appeler load_explainer() au startup.")

    row = {k: client_features[k] for k in FEATURE_ORDER}
    df = pd.DataFrame([row])
    shap_values = _explainer.shap_values(df)

    if hasattr(shap_values, "ndim") and shap_values.ndim == 2:
        values = shap_values[0]
    else:
        values = shap_values

    features_impact = []
    for i, feature_name in enumerate(FEATURE_ORDER):
        shap_val = float(values[i])
        features_impact.append({
            "feature": feature_name,
            "value": client_features[feature_name],
            "shap_value": shap_val,
            "direction": "+" if shap_val > 0 else "-",
        })

    features_impact.sort(key=lambda f: abs(f["shap_value"]), reverse=True)
    return features_impact[:top_n]


if __name__ == "__main__":
    from app.ml.churn_model import load_model, predict_churn

    load_model()
    load_explainer()
    print("Modele + explainer charges.\n")

    client_risque = {
        "anciennete_mois": 18, "produits_detenus": 1, "solde_moyen": 850.0,
        "nb_interactions_90j": 1, "derniere_interaction_jours": 75,
        "age_client": 28, "canal_prefere": 3,
    }

    score = predict_churn(client_risque)
    print(f"Score churn client a risque : {score:.3f}\n")

    top = get_top_features(client_risque, top_n=5)
    print("Top 5 features contributrices :\n")
    for i, f in enumerate(top, 1):
        signe = "pousse vers CHURN" if f["direction"] == "+" else "retient le client"
        print(f"  {i}. {f['feature']:30} = {f['value']:>10} "
              f"| shap={f['shap_value']:+.3f} | {signe}")

    print("\nCes 5 features sont celles qui seront envoyees au LLM par explain_service.")
