"""Détection de dérive des données via Evidently.

Compare les features des 30 derniers jours à une baseline (snapshot
du dataset d'entraînement). Génère un rapport HTML consultable.

"""

from pathlib import Path
from datetime import datetime

from app.config import EVIDENTLY_REPORTS_DIR


def run_drift_report(reference_df, current_df) -> dict:
    """Lance Evidently et retourne un dict de synthèse.

    Args:
        reference_df: DataFrame baseline (données d'entraînement).
        current_df: DataFrame actuel (données récentes).

    Returns:
        dict avec `drift_detected` (bool), `drifted_features` (list),
        `report_path` (str).
    """
    # TODO : from evidently.report import Report
    # TODO : from evidently.metric_preset import DataDriftPreset
    # TODO : report = Report(metrics=[DataDriftPreset()])
    # TODO : report.run(reference_data=reference_df, current_data=current_df)
    # TODO : sauvegarder HTML + extraire métriques
    Path(EVIDENTLY_REPORTS_DIR).mkdir(parents=True, exist_ok=True)
    report_path = f"{EVIDENTLY_REPORTS_DIR}/drift_{datetime.utcnow().isoformat()}.html"
    return {
        "drift_detected": False,
        "drifted_features": [],
        "report_path": report_path,
    }
