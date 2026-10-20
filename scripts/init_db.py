"""Initialise la base SQLite — crée les tables et injecte les données.

Prérequis : avoir lancé scripts/generate_fake_data.py avant.

Usage :
    python scripts/init_db.py
"""

import csv
from pathlib import Path

from app.data.database import init_db, SessionLocal, Client, Conseiller
from app.config import DEMO_USERS


def load_clients_from_csv(path: str, session) -> int:
    """Charge les clients depuis le CSV baseline dans la DB."""
    count = 0
    with open(path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            client = Client(
                id=int(row["id"]),
                nom=row["nom"],
                prenom=row["prenom"],
                region=row["region"],
                anciennete_mois=int(row["anciennete_mois"]),
                produits_detenus=int(row["produits_detenus"]),
                solde_moyen=float(row["solde_moyen"]),
                nb_interactions_90j=int(row["nb_interactions_90j"]),
            )
            session.merge(client)
            count += 1
    session.commit()
    return count


def seed_conseillers(session):
    """Peuple la table conseillers à partir de DEMO_USERS."""
    for username, info in DEMO_USERS.items():
        if info["role"] != "conseiller":
            continue
        c = Conseiller(
            username=username,
            nom_affiche=info["nom_affiche"],
            region=info["region"],
        )
        session.merge(c)
    session.commit()


if __name__ == "__main__":
    print("Création des tables...")
    init_db()

    session = SessionLocal()
    try:
        baseline_path = Path("data/clients_baseline.csv")
        if not baseline_path.exists():
            print("ERREUR : lance d'abord `python scripts/generate_fake_data.py`")
            exit(1)

        n = load_clients_from_csv(str(baseline_path), session)
        print(f"OK — {n} clients insérés depuis baseline.")

        seed_conseillers(session)
        print("OK — conseillers insérés.")
    finally:
        session.close()
