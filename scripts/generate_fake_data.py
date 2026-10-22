"""Genere un dataset de clients bancaires synthetiques.

Produit deux fichiers :
    - data/clients_baseline.csv : baseline pour l'entrainement du modele
    - data/clients_current.csv  : donnees recentes AVEC derive volontaire
"""

import csv
import random
from pathlib import Path

NB_CLIENTS = 1000
REGIONS = ["lille", "marseille"]
NOMS = ["Dupont", "Martin", "Benali", "Diallo", "Kaddouri", "Lefevre", "Nguyen", "Lopez", "Garcia", "Mohamed"]
PRENOMS = ["Marie", "Karim", "Fatou", "Jean", "Yasmine", "Antoine", "Lila", "Mohamed", "Sophie", "Ahmed"]


def _compute_churn_probability(features: dict) -> float:
    """Regle metier avec signal clair et bruit faible.

    Objectif : ~30% de churners avec un pattern apprenable par XGBoost.
    """
    proba = 0.05  # Baseline basse : churn vient des signaux, pas du hasard

    # SIGNAL 1 — Interactions recentes (le plus fort predicteur)
    if features["nb_interactions_90j"] <= 1:
        proba += 0.45
    elif features["nb_interactions_90j"] <= 3:
        proba += 0.25
    elif features["nb_interactions_90j"] <= 5:
        proba += 0.10

    # SIGNAL 2 — Derniere interaction
    if features["derniere_interaction_jours"] > 90:
        proba += 0.30
    elif features["derniere_interaction_jours"] > 45:
        proba += 0.15

    # SIGNAL 3 — Solde moyen
    if features["solde_moyen"] < 1000:
        proba += 0.25
    elif features["solde_moyen"] < 3000:
        proba += 0.12

    # SIGNAL 4 — Produits detenus
    if features["produits_detenus"] == 1:
        proba += 0.20
    elif features["produits_detenus"] == 2:
        proba += 0.08

    # SIGNAL 5 — Age
    if features["age_client"] < 28:
        proba += 0.15
    elif features["age_client"] < 40:
        proba += 0.05

    # SIGNAL 6 — Anciennete
    if features["anciennete_mois"] < 6:
        proba += 0.25
    elif features["anciennete_mois"] < 18:
        proba += 0.12

    # SIGNAL 7 — Canal
    if features["canal_prefere"] == 3:  # telephone
        proba += 0.08

    # Bruit TRES REDUIT pour laisser XGBoost apprendre
    proba += random.gauss(0, 0.05)

    return max(0.0, min(1.0, proba))


def _generate_one_client(client_id: int, seed_offset: int = 0) -> dict:
    random.seed(42 + client_id + seed_offset)
    features = {
        "id": client_id,
        "nom": random.choice(NOMS),
        "prenom": random.choice(PRENOMS),
        "region": random.choice(REGIONS),
        "age_client": random.randint(22, 78),
        "anciennete_mois": random.randint(1, 240),
        "produits_detenus": random.randint(1, 6),
        "solde_moyen": round(max(0, random.gauss(15000, 8000)), 2),
        "nb_interactions_90j": max(0, int(random.gauss(6, 2))),
        "derniere_interaction_jours": max(0, int(random.gauss(20, 15))),
        "canal_prefere": random.choices([0, 1, 2, 3], weights=[20, 30, 40, 10])[0],
    }
    proba = _compute_churn_probability(features)
    features["churn"] = 1 if proba >= 0.5 else 0
    return features


def generate_baseline() -> list[dict]:
    return [_generate_one_client(i, seed_offset=0) for i in range(1, NB_CLIENTS + 1)]


def generate_current(baseline: list[dict]) -> list[dict]:
    random.seed(999)
    current = []
    for base_client in baseline:
        c = dict(base_client)
        c["nb_interactions_90j"] = max(0, int(random.gauss(2, 1.5)))
        c["solde_moyen"] = round(max(0, random.gauss(10000, 12000)), 2)
        c["derniere_interaction_jours"] = max(0, int(random.gauss(35, 20)))
        proba = _compute_churn_probability(c)
        c["churn"] = 1 if proba >= 0.5 else 0
        current.append(c)
    return current


def save_csv(data: list[dict], path: str):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    if not data:
        return
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)


if __name__ == "__main__":
    print("Generation des datasets Tempo Client...")
    print()
    baseline = generate_baseline()
    churn_baseline = sum(c["churn"] for c in baseline)
    print(f"Baseline  : {len(baseline)} clients, {churn_baseline} churners "
          f"({churn_baseline / len(baseline) * 100:.1f}%)")
    current = generate_current(baseline)
    churn_current = sum(c["churn"] for c in current)
    print(f"Current   : {len(current)} clients, {churn_current} churners "
          f"({churn_current / len(current) * 100:.1f}%)")
    save_csv(baseline, "data/clients_baseline.csv")
    save_csv(current, "data/clients_current.csv")
    print()
    print("Fichiers crees :")
    print("  - data/clients_baseline.csv")
    print("  - data/clients_current.csv")
