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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown — chargement des modèles, démarrage scheduler."""
    # TODO : charger les modèles ML (churn, reco, SHAP explainer)
    # TODO : démarrer APScheduler (alertes, drift check, cost tracking)
    # TODO : init DB si absente
    yield
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
# TODO : from app.core.routes import router as core_router
# TODO : app.include_router(core_router)
# TODO : from app.auth.routes import router as auth_router
# TODO : app.include_router(auth_router)


# === Fichiers statiques (fronts conseiller + direction) ===
app.mount("/static", StaticFiles(directory="static"), name="static")


# === Health check ===
@app.get("/health")
def health_check():
    return {"status": "ok", "service": "tempo-client-prod"}
