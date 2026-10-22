"""Entraine les modeles ML de Tempo Client et les sauvegarde en pickle."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pickle

import pandas as pd
import xgboost as xgb
import shap
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, roc_auc_score, classification_report

from app.config import CHURN_MODEL_PATH, SHAP_EXPLAINER_PATH, RECO_MODEL_PATH


FEATURE_COLS = [
    "anciennete_mois",
    "produits_detenus",
    "solde_moyen",
    "nb_interactions_90j",
    "derniere_interaction_jours",
    "age_client",
    "canal_prefere",
]
TARGET_COL = "churn"


def load_baseline() -> pd.DataFrame:
    path = Path("data/clients_baseline.csv")
    if not path.exists():
        print("ERREUR : lance d'abord `python scripts/generate_fake_data.py`")
        raise SystemExit(1)
    return pd.read_csv(path)


def train_churn_model(df: pd.DataFrame) -> xgb.XGBClassifier:
    print("\n--- Entrainement XGBoost churn ---")
    X = df[FEATURE_COLS]
    y = df[TARGET_COL]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y,
    )

    # Calcul du ratio pour compenser le desequilibre de classes
    # scale_pos_weight = nb_negatives / nb_positives
    nb_pos = y_train.sum()
    nb_neg = len(y_train) - nb_pos
    scale_pos_weight = nb_neg / nb_pos if nb_pos > 0 else 1.0

    print(f"Train : {len(X_train)} clients ({nb_pos} churners)")
    print(f"Test  : {len(X_test)} clients ({y_test.sum()} churners)")
    print(f"scale_pos_weight : {scale_pos_weight:.2f}")

    model = xgb.XGBClassifier(
        n_estimators=200,          # Plus d'arbres
        max_depth=5,               # Un peu plus profond
        learning_rate=0.08,
        scale_pos_weight=scale_pos_weight,  # Compense le desequilibre
        random_state=42,
        eval_metric="logloss",
    )
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]
    acc = accuracy_score(y_test, y_pred)
    auc = roc_auc_score(y_test, y_proba)
    print(f"\nAccuracy : {acc:.3f}")
    print(f"AUC-ROC  : {auc:.3f}")
    print("\nClassification report :")
    print(classification_report(y_test, y_pred, target_names=["stable", "churner"]))

    Path(CHURN_MODEL_PATH).parent.mkdir(parents=True, exist_ok=True)
    with open(CHURN_MODEL_PATH, "wb") as f:
        pickle.dump(model, f)
    print(f"Modele sauvegarde : {CHURN_MODEL_PATH}")
    return model


def build_shap_explainer(model: xgb.XGBClassifier, df: pd.DataFrame):
    print("\n--- Construction SHAP explainer ---")
    explainer = shap.TreeExplainer(model)
    X_sample = df[FEATURE_COLS].head(5)
    shap_values = explainer.shap_values(X_sample)
    print(f"Shape des SHAP values : {shap_values.shape}")
    Path(SHAP_EXPLAINER_PATH).parent.mkdir(parents=True, exist_ok=True)
    with open(SHAP_EXPLAINER_PATH, "wb") as f:
        pickle.dump(explainer, f)
    print(f"Explainer sauvegarde : {SHAP_EXPLAINER_PATH}")
    return explainer


def train_reco_model():
    print("\n--- Modele de recommandation (rule-based) ---")
    reco_rules = {
        "version": "1.0",
        "description": "Regles metier pour recommander des actions de retention",
        "rules": [
            {"condition": "score_churn >= 0.7 and solde_moyen >= 10000",
             "action": "RDV conseiller urgent + offre fidelite premium",
             "priorite": "haute",
             "justification": "Client a fort potentiel qui part : action commerciale immediate."},
            {"condition": "score_churn >= 0.7 and solde_moyen < 10000",
             "action": "Appel telephonique + proposition de simplification",
             "priorite": "haute",
             "justification": "Client fragile a reconquerir par la relation."},
            {"condition": "score_churn >= 0.4 and nb_interactions_90j < 3",
             "action": "Email de reactivation + offre decouverte produit",
             "priorite": "moyenne",
             "justification": "Client qui decroche : relancer avant que ce soit trop tard."},
            {"condition": "score_churn >= 0.4",
             "action": "Suivi dans 15 jours + enquete satisfaction",
             "priorite": "moyenne",
             "justification": "Signal faible mais a surveiller."},
            {"condition": "score_churn < 0.4",
             "action": "Pas d'action proactive requise",
             "priorite": "basse",
             "justification": "Client stable, pas d'alerte."},
        ],
    }
    Path(RECO_MODEL_PATH).parent.mkdir(parents=True, exist_ok=True)
    with open(RECO_MODEL_PATH, "wb") as f:
        pickle.dump(reco_rules, f)
    print(f"Regles sauvegardees : {RECO_MODEL_PATH}")


if __name__ == "__main__":
    print("=" * 70)
    print("ENTRAINEMENT DES MODELES ML TEMPO CLIENT")
    print("=" * 70)
    df = load_baseline()
    print(f"\nDataset charge : {len(df)} clients, {df['churn'].sum()} churners "
          f"({df['churn'].mean() * 100:.1f}%)")
    model = train_churn_model(df)
    build_shap_explainer(model, df)
    train_reco_model()
    print()
    print("=" * 70)
    print("OK - Tous les modeles entraines et sauvegardes.")
    print("=" * 70)
