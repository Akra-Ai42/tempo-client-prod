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
    client_id: int
    explication: str = Field(..., description="Explication en langage conseiller")
    model_used: str
    tokens_used: int
    cost_usd: Optional[float] = None


# === Recommandations ===

class Recommandation(BaseModel):
    action: str
    priorite: str = Field(..., description="haute | moyenne | basse")
    justification: str


class RecommendResponse(BaseModel):
    client_id: int
    recommandations: list[Recommandation]


# === Direction Dashboard ===

class DashboardKPI(BaseModel):
    nb_clients_total: int
    nb_clients_risque_haut: int
    nb_clients_risque_moyen: int
    taux_churn_predit: float
    cout_llm_mois_courant_usd: float
    derive_detectee: bool
