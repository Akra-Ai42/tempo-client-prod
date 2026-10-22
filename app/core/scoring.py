"""Service de scoring Tempo Client.

Pre-score tous les clients au demarrage et expose les resultats via
un dict en memoire pour un acces ultra-rapide.

Pattern "pre-compute + cache en memoire" :
    - Au boot, on score les 1000 clients en une passe (~1-2s)
    - A chaque requete /score/{id} ou /clients/mine, on lit du dict
    - Pas d'appel XGBoost ni SHAP pendant les requetes HTTP
"""

import logging
import time
from dataclasses import dataclass
from typing import Optional

from app.core.clients import get_all_clients
from app.ml.churn_model import predict_churn, urgence_from_score
from app.ml.shap_explainer import get_top_features


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ScoreData:
    """Donnees de scoring d'un client (immutable)."""
    client_id: int
    score_churn: float
    urgence: str
    top_features: list[dict]


# Dict en memoire : client_id -> ScoreData
_scored_clients: dict[int, ScoreData] = {}


def precompute_all_scores() -> None:
    """Score tous les clients charges en memoire.

    A appeler UNE FOIS au demarrage de l'application dans le lifespan
    FastAPI, apres load_clients() et apres load_model() + load_explainer().
    """
    global _scored_clients

    clients = get_all_clients()
    logger.info(f"Pre-scoring de {len(clients)} clients...")
    start = time.time()

    scored = {}
    for client in clients:
        # Extraire uniquement les 7 features ML (pas id/nom/prenom/region/churn)
        features = {
            "anciennete_mois": client["anciennete_mois"],
            "produits_detenus": client["produits_detenus"],
            "solde_moyen": client["solde_moyen"],
            "nb_interactions_90j": client["nb_interactions_90j"],
            "derniere_interaction_jours": client["derniere_interaction_jours"],
            "age_client": client["age_client"],
            "canal_prefere": client["canal_prefere"],
        }

        score = predict_churn(features)
        urgence = urgence_from_score(score)
        top = get_top_features(features, top_n=5)

        scored[client["id"]] = ScoreData(
            client_id=client["id"],
            score_churn=score,
            urgence=urgence,
            top_features=top,
        )

    _scored_clients = scored
    duration_s = time.time() - start
    logger.info(
        f"Pre-scoring termine : {len(scored)} clients en {duration_s:.2f}s "
        f"({len(scored) / duration_s:.0f} clients/s)"
    )


def get_score(client_id: int) -> Optional[ScoreData]:
    """Retourne le score precalcule d'un client, ou None si absent."""
    return _scored_clients.get(client_id)


def get_all_scores() -> dict[int, ScoreData]:
    """Retourne tous les scores precalcules (pour /clients/mine enrichi)."""
    return _scored_clients
