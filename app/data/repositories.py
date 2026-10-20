"""Repositories — abstraction sur SQLAlchemy pour que le code métier
ne connaisse pas la DB directement.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.data.database import Client, Conseiller, ScoringHistory, AccessLog


class ClientRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self) -> list[Client]:
        return self.db.query(Client).all()

    def get_by_region(self, region: str) -> list[Client]:
        return self.db.query(Client).filter(Client.region == region).all()

    def get_by_id(self, client_id: int) -> Optional[Client]:
        return self.db.query(Client).filter(Client.id == client_id).first()


class ScoringRepository:
    def __init__(self, db: Session):
        self.db = db

    def save_score(self, client_id: int, score: float, model_version: str = "v1"):
        entry = ScoringHistory(
            client_id=client_id,
            score_churn=score,
            model_version=model_version,
        )
        self.db.add(entry)
        self.db.commit()
        return entry

    def get_latest(self, client_id: int) -> Optional[ScoringHistory]:
        return (
            self.db.query(ScoringHistory)
            .filter(ScoringHistory.client_id == client_id)
            .order_by(ScoringHistory.timestamp.desc())
            .first()
        )


class AccessLogRepository:
    """Repository pour le log d'accès — exploité par l'incident 3."""

    def __init__(self, db: Session):
        self.db = db

    def log_access(
        self,
        username: str,
        user_region: str,
        client_id: int,
        client_region: str,
        endpoint: str,
    ):
        entry = AccessLog(
            username=username,
            user_region=user_region,
            client_id=client_id,
            client_region=client_region,
            endpoint=endpoint,
        )
        self.db.add(entry)
        self.db.commit()
        return entry

    def get_cross_region_accesses(self) -> list[AccessLog]:
        """Retourne les accès où user_region != client_region.

        Dans un système sain, cette liste doit être vide pour les conseillers.
        L'incident 3 fait qu'elle est pleine.
        """
        return (
            self.db.query(AccessLog)
            .filter(AccessLog.user_region != AccessLog.client_region)
            .all()
        )
