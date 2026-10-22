"""Service d'acces aux clients Tempo Client.

Charge le CSV une seule fois au demarrage (lifespan FastAPI) et le garde
en memoire. Pour un POC avec 1000 clients, c'est largement suffisant.
"""

import csv
from pathlib import Path
from typing import Optional


_all_clients: Optional[list[dict]] = None


def load_clients(csv_path: str = "data/clients_baseline.csv") -> None:
    """Charge les clients depuis le CSV en memoire."""
    global _all_clients

    path = Path(csv_path)
    if not path.exists():
        raise RuntimeError(
            f"Fichier clients introuvable : {csv_path}. "
            f"Lancer `python scripts/generate_fake_data.py` d'abord."
        )

    clients = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row["id"] = int(row["id"])
            row["age_client"] = int(row["age_client"])
            row["anciennete_mois"] = int(row["anciennete_mois"])
            row["produits_detenus"] = int(row["produits_detenus"])
            row["solde_moyen"] = float(row["solde_moyen"])
            row["nb_interactions_90j"] = int(row["nb_interactions_90j"])
            row["derniere_interaction_jours"] = int(row["derniere_interaction_jours"])
            row["canal_prefere"] = int(row["canal_prefere"])
            row["churn"] = int(row["churn"])
            clients.append(row)

    _all_clients = clients


def get_all_clients() -> list[dict]:
    """Retourne la liste complete des clients chargee en memoire."""
    if _all_clients is None:
        raise RuntimeError("Clients non charges. Appeler load_clients() au startup.")
    return _all_clients


def get_client_by_id(client_id: int) -> Optional[dict]:
    """Retourne un client par son id, ou None si absent."""
    for c in get_all_clients():
        if c["id"] == client_id:
            return c
    return None
