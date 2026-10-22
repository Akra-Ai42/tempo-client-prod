"""Detection de derive des donnees via Evidently.

Compare les features de clients_current.csv a une baseline (clients_baseline.csv,
snapshot du dataset d'entrainement). Genere un rapport HTML consultable + un
dict de synthese pour le dashboard direction.

Pattern archi : adapter technique Evidently. Le centre (routes.py) consomme
run_drift_report() comme une boite noire. Si demain on remplace Evidently par
Nannyml ou un test custom, on change uniquement ce fichier.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd
from evidently.report import Report
from evidently.metric_preset import DataDriftPreset

from app.config import (
    EVIDENTLY_REPORTS_DIR,
    CLIENTS_BASELINE_CSV,
    CLIENTS_CURRENT_CSV,
)


# === Cache en memoire du dernier rapport ===
# Permet au dashboard de recuperer le resultat instantanement sans recalculer.
# Rafraichi au boot (lifespan) et sur appel manuel de /monitoring/drift/recompute.
_LAST_REPORT: Optional[dict] = None


def get_last_drift_report() -> Optional[dict]:
    """Retourne le dernier rapport en memoire, ou None si jamais calcule."""
    return _LAST_REPORT


# === Features suivies pour la detection ===
# On exclut id/nom/prenom (identifiants), region/canal_prefere (categoriels gerés
# a part), et churn (la cible, pas une feature).
NUMERIC_FEATURES = [
    "age_client",
    "anciennete_mois",
    "produits_detenus",
    "solde_moyen",
    "nb_interactions_90j",
    "derniere_interaction_jours",
]


def run_drift_report(
    reference_df: Optional[pd.DataFrame] = None,
    current_df: Optional[pd.DataFrame] = None,
) -> dict:
    """Lance Evidently DataDriftPreset et retourne un dict de synthese.

    Args:
        reference_df: DataFrame baseline. Si None, charge CLIENTS_BASELINE_CSV.
        current_df: DataFrame actuel. Si None, charge CLIENTS_CURRENT_CSV.

    Returns:
        dict avec :
            - drift_detected (bool) : seuil Evidently par defaut (50% features)
            - nb_features_drifted (int) : nombre de features ayant derive
            - nb_features_total (int) : nombre total de features testees
            - drifted_features (list[str]) : noms des features ayant derive
            - share_drifted (float) : part des features derivees, 0.0 a 1.0
            - report_path (str) : chemin du rapport HTML historise
            - report_latest_path (str) : chemin du rapport HTML "latest"
            - computed_at (str) : ISO datetime du calcul
    """
    global _LAST_REPORT

    # Chargement par defaut si rien n'est passe
    if reference_df is None:
        reference_df = pd.read_csv(CLIENTS_BASELINE_CSV)
    if current_df is None:
        current_df = pd.read_csv(CLIENTS_CURRENT_CSV)

    # On ne garde que les features numeriques pour le drift
    ref = reference_df[NUMERIC_FEATURES].copy()
    cur = current_df[NUMERIC_FEATURES].copy()

    # Preparer le dossier de sortie
    reports_dir = Path(EVIDENTLY_REPORTS_DIR)
    reports_dir.mkdir(parents=True, exist_ok=True)

    # Lancer Evidently
    report = Report(metrics=[DataDriftPreset()])
    report.run(reference_data=ref, current_data=cur)

    # Extraire le resultat JSON (plus fiable que parser le HTML)
    result_json = report.as_dict()

    # Le premier metric est DataDriftTable (ou equivalent) qui contient la synthese
    drift_metric = result_json["metrics"][0]["result"]
    nb_drifted = drift_metric.get("number_of_drifted_columns", 0)
    nb_total = drift_metric.get("number_of_columns", len(NUMERIC_FEATURES))
    share_drifted = drift_metric.get("share_of_drifted_columns", 0.0)
    dataset_drifted = drift_metric.get("dataset_drift", False)

    # Extraire la liste des features derivees (depuis le 2eme metric qui est DataDriftTable)
    drifted_features = []
    try:
        drift_by_columns = result_json["metrics"][1]["result"]["drift_by_columns"]
        drifted_features = [
            feat for feat, data in drift_by_columns.items()
            if data.get("drift_detected", False)
        ]
    except (KeyError, IndexError):
        pass

    # Sauvegarder le rapport HTML : historise + latest
    ts = datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%S")
    report_path_historised = reports_dir / f"drift_{ts}.html"
    report_path_latest = reports_dir / "latest.html"

    report.save_html(str(report_path_historised))
    report.save_html(str(report_path_latest))

    # Construire le dict de synthese
    synthesis = {
        "drift_detected": bool(dataset_drifted),
        "nb_features_drifted": int(nb_drifted),
        "nb_features_total": int(nb_total),
        "drifted_features": drifted_features,
        "share_drifted": round(float(share_drifted), 3),
        "report_path": str(report_path_historised),
        "report_latest_path": str(report_path_latest),
        "computed_at": datetime.utcnow().isoformat(),
    }

    # Memoriser pour acces rapide
    _LAST_REPORT = synthesis

    return synthesis
