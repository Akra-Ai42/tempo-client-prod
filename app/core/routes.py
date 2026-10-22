"""Endpoints metier Tempo Client.

Les 5 endpoints principaux de l'API :
    POST /score/{client_id}      — score churn + top features SHAP (brique 10a) OK
    POST /explain/{client_id}    — explication naturalisee via LLM (brique 10b) OK
    POST /recommend/{client_id}  — recommandations d'actions (brique 10c)
    GET  /clients/mine           — liste clients du conseiller avec scores
    GET  /dashboard/direction    — KPI agreges (reserve direction)
"""

import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.models import User
from app.auth.rbac import filter_clients_by_user, require_direction
from app.auth.session import get_current_user
from app.core.clients import get_all_clients, get_client_by_id
from app.core.explain_service import explain_score
from app.ml.reco_model import recommend_actions
from app.core.schemas import (
    ClientWithUrgence,
    DashboardKPI,
    ExplainResponse,
    MLOpsStats,
    PortfolioStats,
    RecommendResponse,
    ScoreResponse,
    TopClientEntry,
)
from app.core.scoring import get_all_scores, get_score
from app.monitoring.llm_cost import read_cost_log, get_first_of_month, get_24h_ago
from app.llm.base import LLMProviderError
from app.monitoring.audit_log import log_audit_event


logger = logging.getLogger(__name__)
router = APIRouter()

# Timeout global pour un appel LLM depuis cet endpoint (secondes).
# Au-dela, on retourne un fallback texte au lieu de bloquer l'UI du conseiller.
EXPLAIN_TIMEOUT_SECONDS = 30.0


@router.get("/clients/mine", response_model=list[ClientWithUrgence])
async def get_my_clients(user: User = Depends(get_current_user)):
    """Retourne la liste des clients visibles par le conseiller connecte.

    Enrichie avec le score churn et l'urgence depuis le pre-scoring boot.
    """
    all_clients = get_all_clients()
    visible = filter_clients_by_user(all_clients, user)
    scores = get_all_scores()

    enriched = []
    for c in visible:
        score_data = scores.get(c["id"])
        if score_data is None:
            continue
        enriched.append({
            **c,
            "score_churn": score_data.score_churn,
            "urgence": score_data.urgence,
        })

    enriched.sort(key=lambda x: x["score_churn"], reverse=True)
    return [ClientWithUrgence(**c) for c in enriched]


@router.post("/score/{client_id}", response_model=ScoreResponse)
async def get_client_score(
    client_id: int,
    user: User = Depends(get_current_user),
):
    """Retourne le score churn + top 5 features SHAP d'un client."""
    client = get_client_by_id(client_id)
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Client {client_id} introuvable",
        )

    if user.role == "conseiller" and client["region"] != user.region:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acces refuse : ce client n'est pas dans votre perimetre",
        )

    score_data = get_score(client_id)
    if score_data is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Score non precalcule pour ce client (bug serveur)",
        )

    return ScoreResponse(
        client_id=client_id,
        score_churn=score_data.score_churn,
        top_features=score_data.top_features,
    )


@router.post("/explain/{client_id}", response_model=ExplainResponse)
async def get_explanation(
    client_id: int,
    user: User = Depends(get_current_user),
):
    """Genere ou retourne depuis le cache l'explication du score d'un client.

    Pattern hexagonal :
        - RBAC regional : conseiller ne voit que ses clients
        - Score + features SHAP : lus depuis le pre-scoring (brique 10a)
        - Appel LLM via explain_service (brique 2) avec cache TTL
        - Audit RGPD : qui a demande quoi, quand, logue a part
        - Fallback texte si LLM timeout ou erreur
    """
    # 1. Verifier existence client
    client = get_client_by_id(client_id)
    if client is None:
        log_audit_event(
            event_type="explain_requested",
            username=user.username,
            user_role=user.role,
            client_id=client_id,
            outcome="not_found",
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Client {client_id} introuvable",
        )

    # 2. RBAC regional
    if user.role == "conseiller" and client["region"] != user.region:
        log_audit_event(
            event_type="explain_requested",
            username=user.username,
            user_role=user.role,
            client_id=client_id,
            outcome="forbidden",
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acces refuse : ce client n'est pas dans votre perimetre",
        )

    # 3. Recuperer score + top features depuis pre-scoring
    score_data = get_score(client_id)
    if score_data is None:
        log_audit_event(
            event_type="explain_requested",
            username=user.username,
            user_role=user.role,
            client_id=client_id,
            outcome="score_missing",
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Score non precalcule pour ce client (bug serveur)",
        )

    # 4. Appel au service d'explication avec timeout
    try:
        result = await asyncio.wait_for(
            explain_score(
                client_id=client_id,
                client_prenom=client["prenom"],
                client_nom=client["nom"],
                score_churn=score_data.score_churn,
                top_features=score_data.top_features,
            ),
            timeout=EXPLAIN_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError:
        logger.warning(f"LLM timeout for client {client_id} after {EXPLAIN_TIMEOUT_SECONDS}s")
        log_audit_event(
            event_type="explain_requested",
            username=user.username,
            user_role=user.role,
            client_id=client_id,
            outcome="llm_timeout",
        )
        return ExplainResponse(
            client_id=client_id,
            explication=(
                "Explication indisponible pour le moment (delai depasse). "
                "Les facteurs de risque sont visibles dans les top features SHAP ci-dessus. "
                "Reessayez dans quelques instants."
            ),
            from_cache=False,
            latency_ms=int(EXPLAIN_TIMEOUT_SECONDS * 1000),
            cost_usd=0.0,
            model_used=None,
        )
    except LLMProviderError as e:
        logger.error(f"LLM error for client {client_id}: {e}")
        log_audit_event(
            event_type="explain_requested",
            username=user.username,
            user_role=user.role,
            client_id=client_id,
            outcome="llm_error",
            extra={"error": str(e)[:200]},
        )
        return ExplainResponse(
            client_id=client_id,
            explication=(
                "Explication indisponible (erreur du service LLM). "
                "Les facteurs de risque sont visibles dans les top features SHAP ci-dessus."
            ),
            from_cache=False,
            latency_ms=None,
            cost_usd=0.0,
            model_used=None,
        )

    # 5. Succes : logger audit et retourner la reponse enrichie
    log_audit_event(
        event_type="explain_requested",
        username=user.username,
        user_role=user.role,
        client_id=client_id,
        outcome="success",
        extra={"from_cache": result.from_cache, "model": result.model_used},
    )
    return ExplainResponse(
        client_id=client_id,
        explication=result.text,
        from_cache=result.from_cache,
        latency_ms=result.latency_ms,
        cost_usd=result.cost_usd,
        model_used=result.model_used,
    )


# === Endpoints a venir ===


@router.post("/recommend/{client_id}", response_model=RecommendResponse)
async def get_recommendations(
    client_id: int,
    user: User = Depends(get_current_user),
):
    """Recommande jusqu'a 3 actions de retention priorisees pour un client.

    Pattern hexagonal :
        - RBAC regional : conseiller ne voit que ses clients
        - Score + features : lus depuis le pre-scoring (brique 10a)
        - Regles metier : evaluees depuis models/reco_model.pkl
        - Audit RGPD : qui a demande quoi, quand, logue a part
    """
    # 1. Verifier existence client
    client = get_client_by_id(client_id)
    if client is None:
        log_audit_event(
            event_type="recommend_requested",
            username=user.username,
            user_role=user.role,
            client_id=client_id,
            outcome="not_found",
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Client {client_id} introuvable",
        )

    # 2. RBAC regional
    if user.role == "conseiller" and client["region"] != user.region:
        log_audit_event(
            event_type="recommend_requested",
            username=user.username,
            user_role=user.role,
            client_id=client_id,
            outcome="forbidden",
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acces refuse : ce client n'est pas dans votre perimetre",
        )

    # 3. Recuperer score depuis pre-scoring
    score_data = get_score(client_id)
    if score_data is None:
        log_audit_event(
            event_type="recommend_requested",
            username=user.username,
            user_role=user.role,
            client_id=client_id,
            outcome="score_missing",
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Score non precalcule pour ce client (bug serveur)",
        )

    # 4. Appeler le moteur de reco (regles metier sur features + score)
    features = {
        "anciennete_mois": client["anciennete_mois"],
        "produits_detenus": client["produits_detenus"],
        "solde_moyen": client["solde_moyen"],
        "nb_interactions_90j": client["nb_interactions_90j"],
        "derniere_interaction_jours": client["derniere_interaction_jours"],
        "age_client": client["age_client"],
        "canal_prefere": client["canal_prefere"],
    }

    try:
        recos = recommend_actions(features, churn_score=score_data.score_churn)
    except Exception as e:
        logger.error(f"Reco engine error for client {client_id}: {e}")
        log_audit_event(
            event_type="recommend_requested",
            username=user.username,
            user_role=user.role,
            client_id=client_id,
            outcome="reco_error",
            extra={"error": str(e)[:200]},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur du moteur de recommandation",
        )

    # 5. Succes : logger audit et retourner
    log_audit_event(
        event_type="recommend_requested",
        username=user.username,
        user_role=user.role,
        client_id=client_id,
        outcome="success",
        extra={"nb_recos": len(recos)},
    )
    return RecommendResponse(
        client_id=client_id,
        recommandations=recos,
    )


@router.get("/dashboard/direction", response_model=DashboardKPI)
async def get_direction_dashboard(user: User = Depends(require_direction)):
    """Dashboard KPI pour la direction (vue agregee business + ML Ops).

    Compose 3 vues :
        - portfolio : repartition urgence, score moyen, taux churn predit
        - ml_ops : couts LLM (mois + 24h), hit rate cache, latence moyenne
        - top_clients_risque : 10 clients avec le score churn le plus eleve

    Pattern archi :
        - lit les scores depuis le pre-scoring en memoire (brique 10a)
        - lit les couts LLM depuis l'adapter llm_cost (brique 1)
        - lit les clients depuis le singleton clients (brique 5)
        - zero appel ML, zero appel LLM, requete ultra-rapide
    """
    # 1. Portfolio stats depuis le pre-scoring
    all_scores = get_all_scores()
    total = len(all_scores)

    nb_high = sum(1 for s in all_scores.values() if s.urgence == "high")
    nb_medium = sum(1 for s in all_scores.values() if s.urgence == "medium")
    nb_low = sum(1 for s in all_scores.values() if s.urgence == "low")

    score_moyen = (
        sum(s.score_churn for s in all_scores.values()) / total
        if total > 0 else 0.0
    )

    # Taux churn predit = pct des clients avec score >= 0.5 (seuil binaire)
    nb_predicted_churn = sum(1 for s in all_scores.values() if s.score_churn >= 0.5)
    taux_churn_predit = (nb_predicted_churn * 100 / total) if total > 0 else 0.0

    portfolio = PortfolioStats(
        total_clients=total,
        nb_high=nb_high,
        nb_medium=nb_medium,
        nb_low=nb_low,
        pct_high=round(nb_high * 100 / total, 1) if total > 0 else 0.0,
        pct_medium=round(nb_medium * 100 / total, 1) if total > 0 else 0.0,
        pct_low=round(nb_low * 100 / total, 1) if total > 0 else 0.0,
        score_moyen=round(score_moyen, 3),
        taux_churn_predit=round(taux_churn_predit, 1),
    )

    # 2. ML Ops stats depuis le log LLM
    stats_mois = read_cost_log(since=get_first_of_month())
    stats_24h = read_cost_log(since=get_24h_ago())

    ml_ops = MLOpsStats(
        cost_llm_mois_courant_usd=stats_mois["total_cost_usd"],
        cost_llm_24h_usd=stats_24h["total_cost_usd"],
        nb_appels_mois=stats_mois["nb_calls"],
        nb_appels_24h=stats_24h["nb_calls"],
        hit_rate_pct=stats_mois["hit_rate_pct"],
        avg_latency_ms=stats_mois["avg_latency_ms"],
        last_call_at=stats_mois["last_call_at"],
    )

    # 3. Top 10 clients a risque toutes regions
    all_clients = get_all_clients()
    clients_by_id = {c["id"]: c for c in all_clients}

    sorted_scores = sorted(
        all_scores.values(),
        key=lambda s: s.score_churn,
        reverse=True,
    )[:10]

    top_clients = []
    for s in sorted_scores:
        client = clients_by_id.get(s.client_id)
        if client is None:
            continue
        top_clients.append(TopClientEntry(
            id=s.client_id,
            prenom=client["prenom"],
            nom=client["nom"],
            region=client["region"],
            score_churn=round(s.score_churn, 3),
            urgence=s.urgence,
        ))

    return DashboardKPI(
        portfolio=portfolio,
        ml_ops=ml_ops,
        top_clients_risque=top_clients,
    )
