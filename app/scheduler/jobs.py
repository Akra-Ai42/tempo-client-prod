"""Jobs APScheduler pour historisation KPI dashboard direction.

Pattern archi : orchestration. Ce module appelle le centre metier
(get_all_scores, get_all_clients, read_cost_log, run_drift_report) et
delegue le stockage a l adapter db.py. Ne connait pas SQLite directement.

3 taches :
    - snapshot_kpi_job     : toutes les heures, snapshot KPI business + ML Ops
    - daily_drift_job      : tous les jours a 2h du matin, recalcul derive
    - purge_old_data_job   : tous les jours a 3h du matin, retention 90j
"""

import logging
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.scheduler.db import (
    init_db,
    insert_snapshot_kpi,
    insert_drift_snapshot,
    purge_old_snapshots,
)

logger = logging.getLogger(__name__)

# Scheduler singleton partage avec le lifespan FastAPI
_scheduler: AsyncIOScheduler = None


def snapshot_kpi_job() -> None:
    """Capture un snapshot KPI business + ML Ops dans SQLite.

    Lit :
        - Scores pre-calcules via get_all_scores()
        - Couts LLM via read_cost_log(since=mois / since=24h)

    Ecrit :
        - 1 ligne dans snapshots_kpi
    """
    try:
        from app.core.scoring import get_all_scores
        from app.monitoring.llm_cost import (
            read_cost_log,
            get_first_of_month,
            get_24h_ago,
        )

        all_scores = get_all_scores()
        total = len(all_scores)

        if total == 0:
            logger.warning("snapshot_kpi_job : get_all_scores vide, skip")
            return

        nb_high = sum(1 for s in all_scores.values() if s.urgence == "high")
        nb_medium = sum(1 for s in all_scores.values() if s.urgence == "medium")
        nb_low = sum(1 for s in all_scores.values() if s.urgence == "low")

        score_moyen = sum(s.score_churn for s in all_scores.values()) / total
        nb_churn = sum(1 for s in all_scores.values() if s.score_churn >= 0.5)
        taux_churn_predit = (nb_churn * 100 / total)

        stats_mois = read_cost_log(since=get_first_of_month())
        stats_24h = read_cost_log(since=get_24h_ago())

        snapshot = {
            "total_clients": total,
            "nb_high": nb_high,
            "nb_medium": nb_medium,
            "nb_low": nb_low,
            "score_moyen": round(score_moyen, 3),
            "taux_churn_predit": round(taux_churn_predit, 1),
            "cost_llm_mois": stats_mois["total_cost_usd"],
            "cost_llm_24h": stats_24h["total_cost_usd"],
            "nb_appels_24h": stats_24h["nb_calls"],
            "hit_rate_pct": stats_mois["hit_rate_pct"],
            "avg_latency_ms": stats_mois["avg_latency_ms"],
        }

        insert_snapshot_kpi(snapshot)
        logger.info(
            "snapshot_kpi_job OK : total={}, high={}, cost_mois={:.6f} USD".format(
                total, nb_high, stats_mois["total_cost_usd"]
            )
        )
    except Exception as e:
        logger.error(f"snapshot_kpi_job FAILED : {e}", exc_info=True)


def daily_drift_job() -> None:
    """Recalcule le rapport de derive Evidently et le stocke dans drift_history.

    Lit :
        - clients_baseline.csv et clients_current.csv via run_drift_report

    Ecrit :
        - 1 ligne dans drift_history
        - 2 fichiers HTML dans data/evidently_reports/ (latest + historise)
    """
    try:
        from app.monitoring.drift import run_drift_report
        synthesis = run_drift_report()
        insert_drift_snapshot(synthesis)
        logger.info(
            "daily_drift_job OK : detected={}, nb_features={}".format(
                synthesis["drift_detected"], synthesis["nb_features_drifted"]
            )
        )
    except Exception as e:
        logger.error(f"daily_drift_job FAILED : {e}", exc_info=True)


def purge_old_data_job() -> None:
    """Supprime les snapshots KPI de plus de 90 jours.

    La retention snapshot = 90 jours (soit ~2160 lignes au maximum).
    La table drift_history est illimitee (1 ligne/jour = 365 lignes/an).
    """
    try:
        nb_deleted = purge_old_snapshots(days=90)
        logger.info(f"purge_old_data_job OK : {nb_deleted} snapshots supprimes")
    except Exception as e:
        logger.error(f"purge_old_data_job FAILED : {e}", exc_info=True)


def start_scheduler() -> AsyncIOScheduler:
    """Demarre APScheduler avec les 3 taches planifiees.

    A appeler depuis le lifespan FastAPI apres init_db().

    Returns:
        Le scheduler actif.
    """
    global _scheduler

    if _scheduler is not None and _scheduler.running:
        logger.warning("start_scheduler : deja demarre")
        return _scheduler

    init_db()

    _scheduler = AsyncIOScheduler(timezone="UTC")

    # Tache 1 : snapshot KPI toutes les heures
    _scheduler.add_job(
        snapshot_kpi_job,
        trigger=IntervalTrigger(hours=1),
        id="snapshot_kpi",
        name="Snapshot KPI business + ML Ops",
        replace_existing=True,
        max_instances=1,
    )

    # Tache 2 : recalcul derive quotidien a 2h UTC
    _scheduler.add_job(
        daily_drift_job,
        trigger=CronTrigger(hour=2, minute=0),
        id="daily_drift",
        name="Recalcul derive Evidently quotidien",
        replace_existing=True,
        max_instances=1,
    )

    # Tache 3 : purge quotidienne a 3h UTC
    _scheduler.add_job(
        purge_old_data_job,
        trigger=CronTrigger(hour=3, minute=0),
        id="purge_old_data",
        name="Purge snapshots > 90 jours",
        replace_existing=True,
        max_instances=1,
    )

    _scheduler.start()
    logger.info("APScheduler demarre : 3 taches planifiees")

    # Snapshot initial au boot (hors scheduler) pour avoir au moins 1 ligne
    try:
        snapshot_kpi_job()
    except Exception as e:
        logger.warning(f"Snapshot initial au boot a echoue : {e}")

    return _scheduler


def stop_scheduler() -> None:
    """Arrete APScheduler proprement.

    A appeler depuis le shutdown FastAPI.
    """
    global _scheduler
    if _scheduler is not None and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("APScheduler arrete")
