"""Tâches planifiées via APScheduler.

Tâches :
    - alert_risk_shift (toutes les heures) : détecte les clients qui
      viennent de basculer en risque haut et alerte le conseiller.
    - check_drift (quotidien) : lance Evidently sur les features récentes
      vs. baseline → surface l'incident 2.
    - check_llm_cost (toutes les heures) : agrège les coûts du log
      → surface l'incident 1.
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.config import (
    ALERT_CHECK_INTERVAL_MINUTES,
    DRIFT_CHECK_INTERVAL_HOURS,
    TIMEZONE,
)


_scheduler: BackgroundScheduler | None = None


def alert_risk_shift():
    """Détecte les clients qui ont basculé en risque haut récemment."""
    # TODO : requête SQL : clients avec score_churn > 0.7 ET score précédent <= 0.7
    # TODO : logger la liste (pas d'envoi email dans la démo)
    pass


def check_drift():
    """Compare les features récentes à la baseline, génère rapport Evidently."""
    # TODO : charger la baseline + données récentes
    # TODO : Evidently Report → sauvegarder HTML dans EVIDENTLY_REPORTS_DIR
    # TODO : logger "dérive détectée" si > seuil
    pass


def check_llm_cost():
    """Agrège les coûts LLM du mois courant depuis le log JSONL."""
    # TODO : parser LLM_COST_LOG_PATH, filtrer sur le mois courant
    # TODO : calculer le total et logger
    pass


def start_scheduler():
    """Démarre le scheduler — appelé depuis le lifespan de FastAPI."""
    global _scheduler
    _scheduler = BackgroundScheduler(timezone=TIMEZONE)

    _scheduler.add_job(
        alert_risk_shift,
        trigger=IntervalTrigger(minutes=ALERT_CHECK_INTERVAL_MINUTES),
        id="alert_risk_shift",
        replace_existing=True,
    )
    _scheduler.add_job(
        check_drift,
        trigger=IntervalTrigger(hours=DRIFT_CHECK_INTERVAL_HOURS),
        id="check_drift",
        replace_existing=True,
    )
    _scheduler.add_job(
        check_llm_cost,
        trigger=IntervalTrigger(minutes=ALERT_CHECK_INTERVAL_MINUTES),
        id="check_llm_cost",
        replace_existing=True,
    )

    _scheduler.start()


def stop_scheduler():
    """Arrête proprement le scheduler."""
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        _scheduler = None
