"""Traduction des valeurs SHAP en phrases francaises comprehensibles par un conseiller.

Ce module prend le top des features SHAP d'un client (sortie du modele XGBoost + SHAP)
et les traduit en phrases en langage metier banque, avec une justification.

Pas d'appel LLM : la traduction est deterministe, basee sur un mapping explicite
feature -> gabarit de phrase, selon le signe SHAP (positif ou negatif) et la valeur
de la feature pour ce client.

Convention SHAP utilisee ici :
    - direction '+' ou shap_value > 0 : la feature AUGMENTE le risque churn
    - direction '-' ou shap_value < 0 : la feature REDUIT le risque churn
"""

from typing import Any


# === Gabarits de phrases par feature ===
#
# Pour chaque feature connue :
#   - 'positif' : phrase quand la feature augmente le risque (SHAP > 0)
#   - 'negatif' : phrase quand la feature reduit le risque (SHAP < 0)
#   - 'justification' : explication generique "pourquoi c'est important"
#
# Les gabarits utilisent {value} pour injecter la valeur reelle du client.

GABARITS = {
    "anciennete_mois": {
        "positif": "Son anciennete de {value_annees} ans augmente son risque de depart de +{poids} points.",
        "negatif": "Son anciennete de {value_annees} ans reduit son risque de depart de {poids} points.",
        "justification": "Les clients recents partent 3 fois plus souvent dans l annee, les clients fideles restent.",
        "transform_value": "annees",
    },
    "produits_detenus": {
        "positif": "Avec {value} produit detenu, son risque de depart augmente de +{poids} points.",
        "negatif": "Avec {value} produits detenus, son risque de depart diminue de {poids} points.",
        "justification": "Un client avec 3 produits ou plus part 2 fois moins souvent qu un client mono-produit.",
        "transform_value": "int",
    },
    "nb_interactions_90j": {
        "positif": "Son faible nombre d interactions ({value} sur 90 jours) augmente son risque de +{poids} points.",
        "negatif": "Son niveau d interactions ({value} sur 90 jours) reduit son risque de {poids} points.",
        "justification": "Un client qui n interagit pas est un client qui prepare son depart, souvent silencieusement.",
        "transform_value": "int",
    },
    "derniere_interaction_jours": {
        "positif": "Pas de contact depuis {value} jours, cela augmente son risque de +{poids} points.",
        "negatif": "Interaction recente il y a {value} jours, cela reduit son risque de {poids} points.",
        "justification": "Au dela de 60 jours sans contact, le risque de churn double.",
        "transform_value": "int",
    },
    "solde_moyen": {
        "positif": "Son solde moyen faible ({value_euros}) augmente son risque de +{poids} points.",
        "negatif": "Son solde moyen ({value_euros}) reduit son risque de {poids} points.",
        "justification": "Un solde moyen faible signale souvent un client qui vide son compte avant de partir.",
        "transform_value": "euros",
    },
    "age_client": {
        "positif": "Son age ({value} ans) augmente son risque de +{poids} points pour ce profil.",
        "negatif": "Son age ({value} ans) reduit son risque de {poids} points pour ce profil.",
        "justification": "L age modifie les attentes et la mobilite bancaire.",
        "transform_value": "int",
    },
    "canal_prefere": {
        "positif": "Son canal prefere ({value}) augmente son risque de +{poids} points.",
        "negatif": "Son canal prefere ({value}) reduit son risque de {poids} points.",
        "justification": "Le canal utilise reflete le niveau d engagement du client avec la banque.",
        "transform_value": "str",
    },
}


def _format_value(raw_value: Any, transform: str) -> str:
    """Formate la valeur pour affichage dans la phrase."""
    if transform == "annees":
        try:
            annees = int(round(float(raw_value) / 12))
            return str(annees) if annees > 0 else "moins de 1"
        except (TypeError, ValueError):
            return str(raw_value)

    if transform == "euros":
        try:
            n = float(raw_value)
            if n >= 1000:
                return f"{n / 1000:.1f}k euros".replace(".", ",")
            return f"{int(n)} euros"
        except (TypeError, ValueError):
            return str(raw_value)

    if transform == "int":
        try:
            return str(int(float(raw_value)))
        except (TypeError, ValueError):
            return str(raw_value)

    return str(raw_value)


def _poids_from_shap(shap_value: float) -> int:
    """Convertit la shap_value (float en logit) en poids entier
    affichable comme un nombre de points de risque.

    Convention empirique : on multiplie par 100 et on arrondit.
    Ce n est pas un pourcentage exact de probabilite, mais un ordre
    de grandeur comprehensible par un banquier non data-scientist.
    """
    return max(1, int(round(abs(shap_value) * 100)))


def translate_features(
    top_features: list[dict],
    client: dict,
    max_facteurs: int = 5,
) -> list[dict]:
    """Traduit le top des features SHAP en phrases metier.

    Args:
        top_features: liste de dicts avec cles 'feature', 'value', 'shap_value', 'direction'.
                     Format tel que produit par app.ml.shap_explainer.
        client: dict client complet (pour recuperer les valeurs des features).
        max_facteurs: nombre max de facteurs retournes.

    Returns:
        Liste de dicts avec cles :
            - sens : 'positif' (augmente le risque) ou 'negatif' (reduit le risque)
            - phrase : phrase complete en francais
            - justification : courte explication metier
            - poids : nombre de points de risque (entier positif)
            - feature : nom technique de la feature (pour debug)
    """
    resultats = []

    for f in top_features[:max_facteurs]:
        feature_name = f.get("feature")
        if feature_name not in GABARITS:
            # Feature inconnue : on la skip plutot que d afficher du jargon
            continue

        gabarit = GABARITS[feature_name]
        shap_value = float(f.get("shap_value", 0.0))
        direction = f.get("direction", "+" if shap_value > 0 else "-")

        # On recupere la valeur de la feature soit dans top_features soit dans le client
        raw_value = f.get("value")
        if raw_value is None:
            raw_value = client.get(feature_name)

        value_str = _format_value(raw_value, gabarit["transform_value"])
        poids = _poids_from_shap(shap_value)

        if direction == "+":
            sens = "positif"
            template = gabarit["positif"]
        else:
            sens = "negatif"
            template = gabarit["negatif"]

        phrase = template.format(
            value=value_str,
            value_annees=value_str,
            value_euros=value_str,
            poids=poids,
        )

        resultats.append({
            "sens": sens,
            "phrase": phrase,
            "justification": gabarit["justification"],
            "poids": poids,
            "feature": feature_name,
        })

    return resultats
