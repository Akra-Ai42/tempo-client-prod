"""Audit log RGPD pour Tempo Client.

Trace QUI a demande QUOI et QUAND, sur les endpoints metier qui exposent
des donnees clients (/explain, /score, etc.). Permet un audit a posteriori
en cas de controle CNIL ou d'enquete interne.

Format : JSONL (une ligne JSON par evenement) dans data/audit_log.jsonl.
Append-only : jamais de modification ou de suppression, cumul chronologique.

Pattern archi : ce log est au niveau du centre (orchestration metier), pas
au niveau de l'adapter LLM (qui ignore qui est l'user). Separation claire
des responsabilites.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional


logger = logging.getLogger(__name__)

# Chemin du fichier d'audit, cree s'il n'existe pas
AUDIT_LOG_PATH = Path("data") / "audit_log.jsonl"


def log_audit_event(
    event_type: str,
    username: str,
    user_role: str,
    client_id: int,
    outcome: str,
    extra: Optional[dict] = None,
) -> None:
    """Ecrit un evenement d'audit dans le fichier JSONL.

    Args:
        event_type   : type d'action, ex. "explain_requested", "score_requested"
        username     : qui a fait l'action
        user_role    : "conseiller" ou "direction"
        client_id    : sur quel client
        outcome      : "success", "forbidden", "not_found", "llm_timeout"...
        extra        : dict optionnel pour metadonnees supplementaires

    Jamais d'exception leve meme si l'ecriture echoue : l'audit ne doit
    pas bloquer le flux metier. Un log loggger warning est emis a la place.
    """
    try:
        AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "ts": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "username": username,
            "user_role": user_role,
            "client_id": client_id,
            "outcome": outcome,
        }
        if extra:
            record["extra"] = extra
        with AUDIT_LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception as e:
        logger.warning(f"Audit log write failed: {e}")
