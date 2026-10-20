"""Génère un dataset de clients bancaires synthétiques.

Produit deux fichiers :
    - data/clients_baseline.csv : baseline pour l'entraînement
    - data/clients_current.csv  : données récentes AVEC dérive volontaire

⚠️ INCIDENT 2 : la dérive est injectée sur deux features :
    - nb_interactions_90j : shift de la moyenne (6 → 2)
    - solde_moyen         : shift de la variance (plus de queue à gauche)
Les étudiants doivent détecter cette dérive via le rapport Evidently.
"""

import csv
import random
from pathlib import Path

NB_CLIENTS = 1000
REGIONS = ["lille", "marseille"]
NOMS = ["Dupont", "Martin", "Benali", "Diallo", "Kaddouri", "Lefèvre", "Nguyen"]
PRENOMS = ["Marie", "Karim", "Fatou", "Jean", "Yasmine", "Antoine", "Lila"]


def generate_baseline() -> list[dict]:
    """Génère la baseline sans dérive."""
    random.seed(42)
    clients = []
    for i in range(1, NB_CLIENTS + 1):
        clients.append({
            "id": i,
            "nom": random.choice(NOMS),
            "prenom": random.choice(PRENOMS),
            "region": random.choice(REGIONS),
            "anciennete_mois": random.randint(1, 240),
            "produits_detenus": random.randint(1, 6),
            "solde_moyen": round(random.gauss(15000, 8000), 2),
            "nb_interactions_90j": max(0, int(random.gauss(6, 2))),
        })
    return clients


def generate_current(baseline: list[dict]) -> list[dict]:
    """Génère les données récentes avec dérive volontaire."""
    random.seed(123)
    current = []
    for client in baseline:
        c = dict(client)
        # ⚠️ DÉRIVE : baisse des interactions (contexte macro ? bug produit ?)
        c["nb_interactions_90j"] = max(0, int(random.gauss(2, 1.5)))
        # ⚠️ DÉRIVE : solde moyen avec queue à gauche (clients plus pauvres ?)
        c["solde_moyen"] = round(random.gauss(10000, 12000), 2)
        current.append(c)
    return current


def save_csv(data: list[dict], path: str):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    if not data:
        return
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)


if __name__ == "__main__":
    baseline = generate_baseline()
    current = generate_current(baseline)
    save_csv(baseline, "data/clients_baseline.csv")
    save_csv(current, "data/clients_current.csv")
    print(f"OK — {len(baseline)} clients baseline + {len(current)} clients current générés.")
