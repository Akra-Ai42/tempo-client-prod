"""Tracking des coûts LLM — log append-only + agrégation.

Chaque appel LLM depuis l'adapter OpenRouter écrit une ligne JSON dans
LLM_COST_LOG_PATH :
    {"ts": "...", "model": "...", "prompt_tokens": N, "completion_tokens": M, "cost_usd": 0.0123, "endpoint": "/explain/..."}

⚠️ INCIDENT 1 : le cache des explications est cassé, chaque /explain
   refait l'appel LLM même pour les mêmes features. En plus, le prompt
   système a grossi commit après commit. Résultat : la facture OpenRouter
   du mois explose. Le dashboard direction la montre.
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
