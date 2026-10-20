"""Modèle de recommandation d'actions de rétention.

Approche hybride :
    - Règles métier simples pour les cas évidents
    - Classifier léger pour les cas complexes
"""

from app.core.schemas import Recommandation


def recommend_actions(client_features: dict, churn_score: float) -> list[Recommandation]:
    """Retourne la liste des actions recommandées, priorisées.

    Args:
        client_features: profil du client.
        churn_score: score churn calculé.

    Returns:
        Liste de recommandations ordonnées par priorité.
    """
    # TODO : règles métier (ex : si solde élevé + score > 0.7 → RDV conseiller)
    # TODO : classifier léger si règles ambigües
    # TODO : retourner 2-4 actions max, triées par priorité
    raise NotImplementedError("À implémenter en phase 4")
