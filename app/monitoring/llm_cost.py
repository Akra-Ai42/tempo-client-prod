"""Tracking des coûts LLM — log append-only + agrégation.

Chaque appel LLM depuis l'adapter OpenRouter écrit une ligne JSON dans
LLM_COST_LOG_PATH :
    {"ts": "...", "model": "...", "prompt_tokens": N, "completion_tokens": M, "cost_usd": 0.0123, "endpoint": "/explain/..."}

"""

import json
from datetime import datetime
from pathlib import Path

from app.config import LLM_COST_LOG_PATH


def log_llm_call(
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    cost_usd: float,
    endpoint: str,
) -> None:
    """Append une ligne au log JSONL."""
    Path(LLM_COST_LOG_PATH).parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": datetime.utcnow().isoformat(),
        "model": model,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "cost_usd": cost_usd,
        "endpoint": endpoint,
    }
    with open(LLM_COST_LOG_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")


def aggregate_month_cost(year: int, month: int) -> dict:
    """Agrège les coûts d'un mois donné depuis le log."""
    path = Path(LLM_COST_LOG_PATH)
    if not path.exists():
        return {"total_usd": 0.0, "nb_calls": 0, "by_model": {}}

    total = 0.0
    nb_calls = 0
    by_model: dict[str, float] = {}
    with open(path, "r") as f:
        for line in f:
            try:
                entry = json.loads(line)
                ts = datetime.fromisoformat(entry["ts"])
                if ts.year == year and ts.month == month:
                    total += entry.get("cost_usd", 0.0)
                    nb_calls += 1
                    by_model[entry["model"]] = (
                        by_model.get(entry["model"], 0.0) + entry.get("cost_usd", 0.0)
                    )
            except (json.JSONDecodeError, KeyError, ValueError):
                continue
    return {"total_usd": total, "nb_calls": nb_calls, "by_model": by_model}


# === Agregation des couts LLM pour le dashboard direction ===

from datetime import datetime, timedelta
from typing import Optional


def read_cost_log(since: Optional[datetime] = None) -> dict:
    """Lit le log JSONL et agrege les couts LLM depuis une date donnee.

    Args:
        since: datetime UTC. Si None, agrege tout l'historique.

    Returns:
        dict avec :
            - total_cost_usd : somme des couts USD
            - nb_calls       : nombre d'appels
            - avg_latency_ms : latence moyenne en ms
            - hit_rate_pct   : pourcentage d'appels marques from_cache (approximation)
            - last_call_at   : ISO date du dernier appel, ou None

    Pattern archi : lecture seule, pas d'effet de bord. Appelle depuis le
    centre (routes.py) pour construire le dashboard. L'adapter ne connait
    pas qui consomme, le centre ne connait pas comment c'est stocke.
    """
    log_path = Path(LLM_COST_LOG_PATH)
    if not log_path.exists():
        return {
            "total_cost_usd": 0.0,
            "nb_calls": 0,
            "avg_latency_ms": 0,
            "hit_rate_pct": 0.0,
            "last_call_at": None,
        }

    total_cost = 0.0
    nb_calls = 0
    total_latency = 0
    nb_from_cache = 0
    last_call_at = None

    with log_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue

            ts_str = record.get("ts")
            if ts_str and since:
                try:
                    ts = datetime.fromisoformat(ts_str)
                    if ts < since:
                        continue
                except ValueError:
                    pass

            nb_calls += 1
            total_cost += record.get("cost_usd") or 0.0
            total_latency += record.get("latency_ms") or 0
            if record.get("from_cache"):
                nb_from_cache += 1
            if ts_str and (last_call_at is None or ts_str > last_call_at):
                last_call_at = ts_str

    return {
        "total_cost_usd": round(total_cost, 6),
        "nb_calls": nb_calls,
        "avg_latency_ms": round(total_latency / nb_calls) if nb_calls > 0 else 0,
        "hit_rate_pct": round(nb_from_cache * 100 / nb_calls, 1) if nb_calls > 0 else 0.0,
        "last_call_at": last_call_at,
    }


def get_first_of_month() -> datetime:
    """Retourne le datetime UTC du 1er jour du mois courant a 00:00:00."""
    now = datetime.utcnow()
    return datetime(now.year, now.month, 1)


def get_24h_ago() -> datetime:
    """Retourne le datetime UTC d'il y a 24h."""
    return datetime.utcnow() - timedelta(hours=24)


# === Agregation des couts LLM pour le dashboard direction ===

from datetime import datetime, timedelta
from typing import Optional


def read_cost_log(since: Optional[datetime] = None) -> dict:
    """Lit le log JSONL et agrege les couts LLM depuis une date donnee.

    Args:
        since: datetime UTC. Si None, agrege tout l'historique.

    Returns:
        dict avec :
            - total_cost_usd : somme des couts USD
            - nb_calls       : nombre d'appels
            - avg_latency_ms : latence moyenne en ms
            - hit_rate_pct   : pourcentage d'appels marques from_cache
            - last_call_at   : ISO date du dernier appel, ou None

    Pattern archi : lecture seule, pas d'effet de bord. Appele depuis le
    centre (routes.py) pour construire le dashboard. L'adapter ne connait
    pas qui consomme, le centre ne connait pas comment c'est stocke.
    """
    log_path = Path(LLM_COST_LOG_PATH)
    if not log_path.exists():
        return {
            "total_cost_usd": 0.0,
            "nb_calls": 0,
            "avg_latency_ms": 0,
            "hit_rate_pct": 0.0,
            "last_call_at": None,
        }

    total_cost = 0.0
    nb_calls = 0
    total_latency = 0
    nb_from_cache = 0
    last_call_at = None

    with log_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue

            ts_str = record.get("ts")
            if ts_str and since:
                try:
                    ts = datetime.fromisoformat(ts_str)
                    if ts < since:
                        continue
                except ValueError:
                    pass

            nb_calls += 1
            total_cost += record.get("cost_usd") or 0.0
            total_latency += record.get("latency_ms") or 0
            if record.get("from_cache"):
                nb_from_cache += 1
            if ts_str and (last_call_at is None or ts_str > last_call_at):
                last_call_at = ts_str

    return {
        "total_cost_usd": round(total_cost, 6),
        "nb_calls": nb_calls,
        "avg_latency_ms": round(total_latency / nb_calls) if nb_calls > 0 else 0,
        "hit_rate_pct": round(nb_from_cache * 100 / nb_calls, 1) if nb_calls > 0 else 0.0,
        "last_call_at": last_call_at,
    }


def get_first_of_month() -> datetime:
    """Retourne le datetime UTC du 1er jour du mois courant a 00:00:00."""
    now = datetime.utcnow()
    return datetime(now.year, now.month, 1)


def get_24h_ago() -> datetime:
    """Retourne le datetime UTC d'il y a 24h."""
    return datetime.utcnow() - timedelta(hours=24)


# === Agregation des couts LLM pour le dashboard direction ===

from datetime import datetime, timedelta
from typing import Optional


def read_cost_log(since: Optional[datetime] = None) -> dict:
    """Lit le log JSONL et agrege les couts LLM depuis une date donnee.

    Args:
        since: datetime UTC. Si None, agrege tout l'historique.

    Returns:
        dict avec :
            - total_cost_usd : somme des couts USD
            - nb_calls       : nombre d'appels
            - avg_latency_ms : latence moyenne en ms
            - hit_rate_pct   : pourcentage d'appels marques from_cache
            - last_call_at   : ISO date du dernier appel, ou None

    Pattern archi : lecture seule, pas d'effet de bord. Appele depuis le
    centre (routes.py) pour construire le dashboard. L'adapter ne connait
    pas qui consomme, le centre ne connait pas comment c'est stocke.
    """
    log_path = Path(LLM_COST_LOG_PATH)
    if not log_path.exists():
        return {
            "total_cost_usd": 0.0,
            "nb_calls": 0,
            "avg_latency_ms": 0,
            "hit_rate_pct": 0.0,
            "last_call_at": None,
        }

    total_cost = 0.0
    nb_calls = 0
    total_latency = 0
    nb_from_cache = 0
    last_call_at = None

    with log_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue

            ts_str = record.get("ts")
            if ts_str and since:
                try:
                    ts = datetime.fromisoformat(ts_str)
                    if ts < since:
                        continue
                except ValueError:
                    pass

            nb_calls += 1
            total_cost += record.get("cost_usd") or 0.0
            total_latency += record.get("latency_ms") or 0
            if record.get("from_cache"):
                nb_from_cache += 1
            if ts_str and (last_call_at is None or ts_str > last_call_at):
                last_call_at = ts_str

    return {
        "total_cost_usd": round(total_cost, 6),
        "nb_calls": nb_calls,
        "avg_latency_ms": round(total_latency / nb_calls) if nb_calls > 0 else 0,
        "hit_rate_pct": round(nb_from_cache * 100 / nb_calls, 1) if nb_calls > 0 else 0.0,
        "last_call_at": last_call_at,
    }


def get_first_of_month() -> datetime:
    """Retourne le datetime UTC du 1er jour du mois courant a 00:00:00."""
    now = datetime.utcnow()
    return datetime(now.year, now.month, 1)


def get_24h_ago() -> datetime:
    """Retourne le datetime UTC d'il y a 24h."""
    return datetime.utcnow() - timedelta(hours=24)
