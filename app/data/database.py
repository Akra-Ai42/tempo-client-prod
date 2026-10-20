"""Session SQLAlchemy, moteur, création des tables.

Schéma :
    - clients            : profils clients bancaires
    - conseillers        : identité et région des conseillers
    - scoring_history    : historique des scores churn (pour audit + dérive)
    - access_log         : log des accès aux fiches clients (audit RBAC)
    - llm_cost_log       : log des appels LLM avec coûts (incident 1)
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from datetime import datetime

from app.config import DATABASE_URL


engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # Nécessaire pour SQLite + FastAPI
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


class Client(Base):
    __tablename__ = "clients"
    id = Column(Integer, primary_key=True)
    nom = Column(String, nullable=False)
    prenom = Column(String, nullable=False)
    region = Column(String, nullable=False, index=True)
    anciennete_mois = Column(Integer, nullable=False)
    produits_detenus = Column(Integer, nullable=False)
    solde_moyen = Column(Float, nullable=False)
    nb_interactions_90j = Column(Integer, nullable=False, default=0)
    derniere_interaction = Column(DateTime, nullable=True)


class Conseiller(Base):
    __tablename__ = "conseillers"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    nom_affiche = Column(String, nullable=False)
    region = Column(String, nullable=False)


class ScoringHistory(Base):
    __tablename__ = "scoring_history"
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, nullable=False, index=True)
    score_churn = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    model_version = Column(String, nullable=False, default="v1")


class AccessLog(Base):
    """Log des accès aux fiches clients — sert à détecter l'incident 3."""
    __tablename__ = "access_log"
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    username = Column(String, nullable=False, index=True)
    user_region = Column(String, nullable=False)
    client_id = Column(Integer, nullable=False, index=True)
    client_region = Column(String, nullable=False)
    endpoint = Column(String, nullable=False)


def init_db():
    """Crée toutes les tables si elles n'existent pas."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dépendance FastAPI — session DB par requête."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
