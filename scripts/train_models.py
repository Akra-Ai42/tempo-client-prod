"""Entraîne les modèles ML et les sauvegarde dans ./models/.

Modèles entraînés :
    - XGBoost binary classifier → predict_churn
    - SHAP TreeExplainer         → explication locale
    - Classifier simple de reco  → recommandations

Prérequis : avoir lancé generate_fake_data.py et init_db.py avant.

Usage :
    python scripts/train_models.py
"""

import pickle
from pathlib import Path

from app.config import CHURN_MODEL_PATH, SHAP_EXPLAINER_PATH, RECO_MODEL_PATH


FEATURE_COLS = [
    "anciennete_mois",
    "produits_detenus",
    "solde_moyen",
    "nb_interactions_90j",
]


def train_churn_model():
    """Entraîne un XGBoost binary classifier sur la baseline."""
    # TODO : charger data/clients_baseline.csv
    # TODO : générer la target churn (règle synthétique : clients avec peu d'interactions
    #        et solde en baisse → churn probable)
    # TODO : train XGBoost + sauvegarder
    print(f"TODO — entraîner et sauvegarder dans {CHURN_MODEL_PATH}")


def build_shap_explainer():
    """Construit un SHAP TreeExplainer à partir du modèle XGBoost."""
    # TODO : charger le modèle, construire shap.TreeExplainer, pickle
    print(f"TODO — construire et sauvegarder dans {SHAP_EXPLAINER_PATH}")


def train_reco_model():
    """Entraîne un classifier léger pour les recommandations."""
    # TODO : définir les actions (RDV, offre, email) + règles
    # TODO : classifier ou dict de règles → sauvegarder
    print(f"TODO — entraîner et sauvegarder dans {RECO_MODEL_PATH}")


if __name__ == "__main__":
    Path("models").mkdir(exist_ok=True)
    train_churn_model()
    build_shap_explainer()
    train_reco_model()
    print("OK — tous les modèles entraînés.")
