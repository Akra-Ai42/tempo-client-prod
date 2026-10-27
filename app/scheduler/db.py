"""Adapter SQLite pour l'historisation des KPI dashboard direction.

Pattern archi : adapter technique. Ne connait ni le dashboard ni les
endpoints. Si demain on migre SQLite vers PostgreSQL ou DuckDB, on
change uniquement ce fichier.

Schema :
    snapshots_kpi : 1 ligne par heure
        ts, total_clients, nb_high, nb_medium, nb_low,
        score_moyen, taux_churn_predit,
        cost_llm_mois, cost_llm_24h, nb_appels_24h,
        hit_rate_pct, avg_latency_ms

    drift_history : 1 ligne par run quotidien
        ts, drift_detected, nb_features_drifted, share_drifted,
        drifted_features (JSON string), report_path
"""

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from app.config import DATA_DIR

DB_PATH = Path(DATA_DIR) / "tempo.db"


@contextmanager
def get_conn():
    """Context manager pour une connexion SQLite."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    """Cree les tables si elles n existent pas. Appele au boot."""
    Path(DATA_DIR).mkdir(parents=True, exist_ok=True)

    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS snapshots_kpi (
                ts TEXT PRIMARY KEY,
                total_clients INTEGER,
                nb_high INTEGER,
                nb_medium INTEGER,
                nb_low INTEGER,
                score_moyen REAL,
                taux_churn_predit REAL,
                cost_llm_mois REAL,
                cost_llm_24h REAL,
                nb_appels_24h INTEGER,
                hit_rate_pct REAL,
                avg_latency_ms INTEGER
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_snapshots_ts
            ON snapshots_kpi(ts DESC)
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS drift_history (
                ts TEXT PRIMARY KEY,
                drift_detected INTEGER,
                nb_features_drifted INTEGER,
                share_drifted REAL,
                drifted_features TEXT,
                report_path TEXT
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_drift_ts
            ON drift_history(ts DESC)
        """)


def insert_snapshot_kpi(snapshot: dict) -> None:
    """Insere un snapshot KPI dans la table.

    Args:
        snapshot: dict avec les 12 cles de la table snapshots_kpi
                  (hormis ts qui est auto-genere)
    """
    ts = datetime.utcnow().isoformat()
    with get_conn() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO snapshots_kpi (
                ts, total_clients, nb_high, nb_medium, nb_low,
                score_moyen, taux_churn_predit,
                cost_llm_mois, cost_llm_24h, nb_appels_24h,
                hit_rate_pct, avg_latency_ms
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            ts,
            snapshot.get("total_clients", 0),
            snapshot.get("nb_high", 0),
            snapshot.get("nb_medium", 0),
            snapshot.get("nb_low", 0),
            snapshot.get("score_moyen", 0.0),
            snapshot.get("taux_churn_predit", 0.0),
            snapshot.get("cost_llm_mois", 0.0),
            snapshot.get("cost_llm_24h", 0.0),
            snapshot.get("nb_appels_24h", 0),
            snapshot.get("hit_rate_pct", 0.0),
            snapshot.get("avg_latency_ms", 0),
        ))


def insert_drift_snapshot(drift: dict) -> None:
    """Insere un snapshot de drift dans drift_history."""
    ts = datetime.utcnow().isoformat()
    with get_conn() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO drift_history (
                ts, drift_detected, nb_features_drifted,
                share_drifted, drifted_features, report_path
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            ts,
            1 if drift.get("drift_detected") else 0,
            drift.get("nb_features_drifted", 0),
            drift.get("share_drifted", 0.0),
            json.dumps(drift.get("drifted_features", [])),
            drift.get("report_path", ""),
        ))


def query_trends(hours: int = 24) -> list[dict]:
    """Retourne les snapshots KPI des N dernieres heures.

    Args:
        hours: fenetre temporelle en heures (defaut 24)

    Returns:
        list de dicts, un par snapshot, ordre chronologique
    """
    since = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT * FROM snapshots_kpi
            WHERE ts >= ?
            ORDER BY ts ASC
        """, (since,)).fetchall()
        return [dict(row) for row in rows]


def query_drift_history(limit: int = 30) -> list[dict]:
    """Retourne les N dernieres entrees de drift_history."""
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT * FROM drift_history
            ORDER BY ts DESC
            LIMIT ?
        """, (limit,)).fetchall()
        result = []
        for row in rows:
            d = dict(row)
            try:
                d["drifted_features"] = json.loads(d.get("drifted_features", "[]"))
            except (json.JSONDecodeError, TypeError):
                d["drifted_features"] = []
            d["drift_detected"] = bool(d["drift_detected"])
            result.append(d)
        return result


def purge_old_snapshots(days: int = 90) -> int:
    """Supprime les snapshots KPI plus vieux que N jours.

    Returns:
        Nombre de lignes supprimees.
    """
    cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
    with get_conn() as conn:
        cursor = conn.execute("""
            DELETE FROM snapshots_kpi WHERE ts < ?
        """, (cutoff,))
        return cursor.rowcount
