"""Middleware RBAC — contrôle d'accès basé sur les rôles.

Règles :
    - Routes publiques : /, /health, /auth/login, /static/*
    - Routes authentifiées : nécessitent un user en session
    - Routes "direction" : nécessitent le rôle direction
    - Routes "mes clients" : filtrées par région du conseiller

⚠️ INCIDENT 3 : la condition de filtrage par région est inversée dans
   ce fichier. Le conseiller Lille voit les clients Marseille et vice-versa.
   À détecter par les étudiants au cours de la semaine Devoteam.
"""

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import DEMO_USERS


# Routes publiques — ne nécessitent pas d'auth
PUBLIC_PATHS = {
    "/",
    "/health",
    "/auth/login",
    "/favicon.ico",
}

# Préfixes publics
PUBLIC_PREFIXES = (
    "/static/",
    "/docs",
    "/openapi.json",
    "/redoc",
)

# Routes réservées à la direction
DIRECTION_ONLY_PREFIXES = (
    "/dashboard/direction",
)


def _is_public(path: str) -> bool:
    if path in PUBLIC_PATHS:
        return True
    return any(path.startswith(p) for p in PUBLIC_PREFIXES)


class RBACMiddleware(BaseHTTPMiddleware):
    """Vérifie l'authentification et les permissions sur chaque requête."""

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        if _is_public(path):
            return await call_next(request)

        # Vérifier qu'un user est en session
        username = request.session.get("username")
        if not username:
            return JSONResponse(
                status_code=401,
                content={"detail": "Authentification requise"},
            )

        user = DEMO_USERS.get(username)
        if not user:
            return JSONResponse(
                status_code=401,
                content={"detail": "Session invalide"},
            )

        # Routes réservées direction
        if any(path.startswith(p) for p in DIRECTION_ONLY_PREFIXES):
            if user["role"] != "direction":
                return JSONResponse(
                    status_code=403,
                    content={"detail": "Accès refusé — réservé à la direction"},
                )

        # Pose user sur la request pour les endpoints
        request.state.user = user
        return await call_next(request)


def filter_clients_by_region(user: dict, all_clients: list) -> list:
    """Filtre la liste des clients selon la région du conseiller.

    ⚠️ INCIDENT 3 : la condition est inversée (!= au lieu de ==).
    Le conseiller Lille voit les clients de TOUTES les régions SAUF Lille.
    Donc il voit Marseille. Et le conseiller Marseille voit Lille.
    Bug subtil que les étudiants doivent détecter en lisant les logs d'accès.

    Args:
        user: dict du user depuis session.
        all_clients: liste complète des clients.

    Returns:
        Liste filtrée.
    """
    if user["role"] == "direction":
        return all_clients  # La direction voit tout

    # ⚠️ BUG VOLONTAIRE — devrait être `== user["region"]`
    return [c for c in all_clients if c["region"] != user["region"]]
