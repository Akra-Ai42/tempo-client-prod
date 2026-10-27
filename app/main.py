"""Point d'entrée FastAPI pour Tempo Client.

Monte les middlewares (session, RBAC), les routers métier, les fichiers
statiques, et le scheduler de tâches.

Lancement en dev :
    uvicorn app.main:app --reload --port 8000

Lancement en prod (Render) :
    uvicorn app.main:app --host 0.0.0.0 --port $PORT
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.config import SESSION_SECRET, SESSION_COOKIE_NAME, SESSION_MAX_AGE
from app.core.clients import load_clients
from app.core.scoring import precompute_all_scores
from app.ml.churn_model import load_model
from app.ml.shap_explainer import load_explainer
from app.ml.reco_model import load_reco_rules
from app.monitoring.drift import run_drift_report
from app.scheduler.jobs import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown — chargement des modèles, démarrage scheduler."""
    # Charger les clients en mémoire depuis le CSV
    load_clients()
    # Charger les modeles ML + SHAP explainer
    load_model()
    load_explainer()
    load_reco_rules()
    # Pre-scorer tous les clients (lecture rapide depuis dict en memoire)
    precompute_all_scores()
    # Brique 8 : calcul initial du rapport de derive Evidently
    try:
        run_drift_report()
    except Exception as e:
        print(f"[WARN] run_drift_report au boot a echoue : {e}")
        # On ne bloque pas le boot si Evidently echoue

    # Brique 9 : demarrer APScheduler (snapshots horaires + drift quotidien + purge)
    try:
        start_scheduler()
        print("[OK] APScheduler demarre : snapshots horaires + drift quotidien")
    except Exception as e:
        print(f"[WARN] start_scheduler a echoue : {e}")
        # On ne bloque pas le boot si le scheduler echoue
    # TODO : démarrer APScheduler (alertes, drift check, cost tracking)
    # TODO : init DB si absente
    yield
    # Brique 9 : arreter APScheduler proprement au shutdown
    try:
        stop_scheduler()
        print("[OK] APScheduler arrete")
    except Exception as e:
        print(f"[WARN] stop_scheduler a echoue : {e}")
    # TODO : flush logs, arrêter scheduler proprement


app = FastAPI(
    title="Tempo Client — Prod",
    description="Outil décisionnel pour conseillers bancaires",
    version="0.1.0",
    lifespan=lifespan,
)


# === Middlewares ===
app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET,
    session_cookie=SESSION_COOKIE_NAME,
    max_age=SESSION_MAX_AGE,
)

# TODO : ajouter le RBACMiddleware (app/auth/rbac.py)
# ATTENTION : c'est dans ce middleware que vit l'incident 3


# === Routers ===
from app.core.routes import router as core_router
app.include_router(core_router)
from app.auth.routes import router as auth_router
app.include_router(auth_router)


# === Fichiers statiques (fronts conseiller + direction) ===
app.mount("/static", StaticFiles(directory="static"), name="static")


# === Health check ===
@app.get("/health")
def health_check():
    return {"status": "ok", "service": "tempo-client-prod"}
