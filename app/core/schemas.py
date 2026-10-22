"""Modèles Pydantic — validation des requêtes et réponses API.

Leçon LÉON acquise : TOUS les endpoints FastAPI valident leurs entrées
et sorties via Pydantic. Pas de `payload: dict = Body(...)` ici.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# === Clients ===

class ClientBase(BaseModel):
    id: int
    nom: str
    prenom: str
    region: str
    anciennete_mois: int
    produits_detenus: int
    solde_moyen: float


class ClientWithScore(ClientBase):
    """Client enrichi de son score churn et de l'urgence associée."""
    score_churn: float = Field(..., ge=0.0, le=1.0)
    urgence: str = Field(..., description="low | medium | high")
    derniere_interaction: Optional[datetime] = None


# === Scoring ===

class ScoreResponse(BaseModel):
    client_id: int
    score_churn: float = Field(..., ge=0.0, le=1.0)
    top_features: list[dict] = Field(
        ..., description="Top 5 features SHAP avec leur contribution"
    )


# === Explication LLM ===

class ExplainResponse(BaseModel):
    """Explication SHAP en langage naturel via LLM.

    Contient l'explication texte + les metadonnees de l'appel LLM
    (cache HIT/MISS, latence, cout) pour transparence et audit.
    """
    client_id: int
    explication: str
    from_cache: bool
    latency_ms: Optional[int] = None
    cost_usd: Optional[float] = None
    model_used: Optional[str] = None
# === Recommandations ===

class Recommandation(BaseModel):
    action: str
    priorite: str = Field(..., description="haute | moyenne | basse")
    justification: str


class RecommendResponse(BaseModel):
    client_id: int
    recommandations: list[Recommandation]


# === Direction Dashboard ===

class TopClientEntry(BaseModel):
    """Entry du top 10 clients a risque pour le dashboard direction."""
    id: int
    prenom: str
    nom: str
    region: str
    score_churn: float
    urgence: str


class PortfolioStats(BaseModel):
    """Statistiques business du portefeuille clients."""
    total_clients: int
    nb_high: int
    nb_medium: int
    nb_low: int
    pct_high: float
    pct_medium: float
    pct_low: float
    score_moyen: float
    taux_churn_predit: float


class MLOpsStats(BaseModel):
    """Statistiques techniques du systeme ML + LLM."""
    cost_llm_mois_courant_usd: float
    cost_llm_24h_usd: float
    nb_appels_mois: int
    nb_appels_24h: int
    hit_rate_pct: float
    avg_latency_ms: int
    last_call_at: Optional[str] = None


class DashboardKPI(BaseModel):
    """Reponse complete du dashboard direction.

    Agrege 3 vues :
        - portfolio : KPI business pour le Comex
        - ml_ops    : KPI techniques pour la DSI
        - top_clients_risque : top 10 clients a risque toutes regions
    """
    portfolio: PortfolioStats
    ml_ops: MLOpsStats
    top_clients_risque: list[TopClientEntry]


# === Client Summary (listing léger sans scoring) ===

class ClientSummary(BaseModel):
    """Résumé client pour les listings — pas de scoring à ce stade.

    Utilisé par GET /clients/mine qui retourne la liste des clients
    du conseiller SANS appeler XGBoost pour chaque client (coûteux
    sur 500+ clients). Le score sera obtenu via /score/{client_id}
    au clic du conseiller.
    """
    id: int
    nom: str
    prenom: str
    region: str
    age_client: int
    anciennete_mois: int
    produits_detenus: int
    solde_moyen: float
    nb_interactions_90j: int
    derniere_interaction_jours: int


# === Client Summary enrichi avec score (brique 10a) ===

class ClientWithUrgence(ClientSummary):
    """ClientSummary + score et urgence depuis le pre-scoring.

    Utilise par /clients/mine pour afficher les scores dans la liste
    sans faire 500 appels XGBoost (ils sont precalcules au boot).
    """
    score_churn: float = Field(..., ge=0.0, le=1.0)
    urgence: str = Field(..., description="low | medium | high")
