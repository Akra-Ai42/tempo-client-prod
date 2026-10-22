"""Moteur de recommandation d'actions de retention.

Approche : regles metier chargees depuis models/reco_model.pkl, evaluees
dans un contexte Python restreint sur les features du client + le score.

Format du pkl :
    {
        'version': '1.0',
        'description': '...',
        'rules': [
            {'condition': 'score_churn >= 0.7 and solde_moyen >= 10000',
             'action': '...', 'priorite': 'haute', 'justification': '...'},
            ...
        ]
    }

Securite :
    eval() est restreint a __builtins__ vide + le dict de features du client
    + le score. Les regles sont ecrites par le data scientist, pas par un user.
    Flux auditable, pas d'input utilisateur dans la condition.
"""

import logging
import pickle
from pathlib import Path
from typing import Optional

from app.core.schemas import Recommandation


logger = logging.getLogger(__name__)

RECO_MODEL_PATH = Path("models") / "reco_model.pkl"

# Ordre de tri des priorites (haute d'abord, basse en dernier)
PRIORITY_ORDER = {"haute": 0, "moyenne": 1, "basse": 2}

# Nombre maximum de recommandations retournees
MAX_RECOMMENDATIONS = 3

# Dict de regles charge en memoire au boot
_reco_rules: Optional[dict] = None


def load_reco_rules() -> None:
    """Charge les regles de recommandation depuis le pkl.

    A appeler UNE FOIS au demarrage de l'app dans le lifespan FastAPI.
    """
    global _reco_rules
    if not RECO_MODEL_PATH.exists():
        raise FileNotFoundError(f"{RECO_MODEL_PATH} introuvable")

    with RECO_MODEL_PATH.open("rb") as f:
        _reco_rules = pickle.load(f)

    rules_count = len(_reco_rules.get("rules", []))
    version = _reco_rules.get("version", "unknown")
    logger.info(f"Reco rules chargees (version {version}, {rules_count} regles)")


def _evaluate_rule(condition: str, context: dict) -> bool:
    """Evalue la condition d'une regle dans un contexte restreint.

    Retourne False silencieusement si l'eval leve une exception
    (regle mal formee, feature manquante, etc.).
    """
    try:
        # eval restreint : pas de builtins, contexte = features + score
        return bool(eval(condition, {"__builtins__": {}}, context))
    except Exception as e:
        logger.warning(f"Regle non evaluable : {condition!r} -> {e}")
        return False


def recommend_actions(
    client_features: dict,
    churn_score: float,
) -> list[Recommandation]:
    """Retourne jusqu'a 3 actions recommandees, triees par priorite.

    Args:
        client_features: dict avec les features ML du client (anciennete_mois,
                         produits_detenus, solde_moyen, nb_interactions_90j,
                         derniere_interaction_jours, age_client, canal_prefere)
        churn_score    : score churn predit par XGBoost, entre 0.0 et 1.0

    Returns:
        Liste de 0 a 3 Recommandation, triee priorite decroissante (haute d'abord).

    Raises:
        RuntimeError si load_reco_rules() n'a pas ete appele au prealable.
    """
    if _reco_rules is None:
        raise RuntimeError("Reco rules non chargees. Appeler load_reco_rules() au boot.")

    # Contexte eval = features + score (accessible via score_churn dans les regles)
    context = {**client_features, "score_churn": churn_score}

    # Evaluer toutes les regles, garder celles qui matchent
    matched = [
        rule for rule in _reco_rules.get("rules", [])
        if _evaluate_rule(rule["condition"], context)
    ]

    # Trier par priorite (haute > moyenne > basse)
    matched.sort(key=lambda r: PRIORITY_ORDER.get(r["priorite"], 99))

    # Limiter a 3 et transformer en Recommandation Pydantic
    return [
        Recommandation(
            action=r["action"],
            priorite=r["priorite"],
            justification=r["justification"],
        )
        for r in matched[:MAX_RECOMMENDATIONS]
    ]
