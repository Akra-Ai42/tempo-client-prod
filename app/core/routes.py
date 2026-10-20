"""Endpoints métier Tempo Client.

Les 5 endpoints principaux de l'API :
    POST /score/{client_id}      — score churn + top features SHAP
    POST /explain/{client_id}    — explication naturalisée via LLM
    POST /recommend/{client_id}  — recommandations d'actions
    GET  /clients/mine           — liste clients du conseiller (filtré RBAC)
    GET  /dashboard/direction    — KPI agrégés (filtré RBAC direction)

Validation Pydantic sur chaque endpoint.
"""

from fastapi import APIRouter, HTTPException, Request

from app.core.schemas import (
    ClientWithScore,
    ScoreResponse,
    ExplainResponse,
    RecommendResponse,
    DashboardKPI,
)

router = APIRouter()


@router.post("/score/{client_id}", response_model=ScoreResponse)
async def get_score(client_id: int, request: Request):
    """Calcule le score churn d'un client + top features SHAP."""
    # TODO : vérifier RBAC (le conseiller ne scorer que ses clients)
    # TODO : charger les features du client depuis la DB
    # TODO : appeler le modèle XGBoost → score
    # TODO : appeler le SHAP explainer → top 5 features
    # TODO : logger dans scoring_history
    raise HTTPException(status_code=501, detail="À implémenter en phase 4")


@router.post("/explain/{client_id}", response_model=ExplainResponse)
async def get_explanation(client_id: int, request: Request):
    """Génère une explication SHAP en langage conseiller via LLM."""
    # TODO : charger les top features SHAP depuis le dernier scoring
    # TODO : construire le prompt (explication naturalisée)
    # TODO : appeler get_llm_provider().complete(...)
    # TODO : logger le coût LLM
    # ⚠️ INCIDENT 1 : cache cassé ici, chaque appel refait l'inférence
    # ⚠️ INCIDENT 1 : le prompt système a gonflé commit après commit
    raise HTTPException(status_code=501, detail="À implémenter en phase 4")


@router.post("/recommend/{client_id}", response_model=RecommendResponse)
async def get_recommendations(client_id: int, request: Request):
    """Recommande des actions de rétention pour un client à risque."""
    # TODO : charger le profil client + score + top features
    # TODO : appliquer le modèle de reco (règles ou classifier léger)
    # TODO : retourner la liste des actions priorisées
    raise HTTPException(status_code=501, detail="À implémenter en phase 4")


@router.get("/clients/mine", response_model=list[ClientWithScore])
async def get_my_clients(request: Request):
    """Retourne la liste des clients du conseiller, filtrée par région.

    ⚠️ INCIDENT 3 : condition inversée dans le RBAC middleware → le
    conseiller Lille peut voir les clients de Marseille et inversement.
    """
    # TODO : récupérer le user depuis request.session
    # TODO : filtrer les clients par région selon le rôle
    # TODO : enrichir avec le score churn et l'urgence
    raise HTTPException(status_code=501, detail="À implémenter en phase 4")


@router.get("/dashboard/direction", response_model=DashboardKPI)
async def get_direction_dashboard(request: Request):
    """Dashboard KPI pour la direction marketing (vue agrégée)."""
    # TODO : vérifier que le user a le rôle "direction"
    # TODO : agréger les stats
    # TODO : inclure l'indicateur de dérive (incident 2)
    # TODO : inclure le coût LLM du mois courant (incident 1)
    raise HTTPException(status_code=501, detail="À implémenter en phase 4")
