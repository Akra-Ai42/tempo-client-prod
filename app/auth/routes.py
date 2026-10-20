"""Endpoints d'authentification — login / logout.

Auth simplifiée pour la démo : 3 users en dur dans la config,
mot de passe en clair (⚠️ démo uniquement).

En production réelle :
    - Users en DB avec password hashé (bcrypt / argon2)
    - JWT ou OAuth2
    - Rate limiting sur /login
    - Audit log des connexions
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.config import DEMO_USERS

router = APIRouter()


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    ok: bool
    role: str
    region: str | None
    nom_affiche: str


@router.post("/auth/login", response_model=LoginResponse)
async def login(payload: LoginRequest, request: Request):
    """Vérifie les identifiants et pose un cookie de session."""
    user = DEMO_USERS.get(payload.username)
    if not user or user["password"] != payload.password:
        raise HTTPException(status_code=401, detail="Identifiants invalides")

    # Pose les infos du user en session (cookie signé)
    request.session["username"] = payload.username
    request.session["role"] = user["role"]
    request.session["region"] = user["region"]

    return LoginResponse(
        ok=True,
        role=user["role"],
        region=user["region"],
        nom_affiche=user["nom_affiche"],
    )


@router.post("/auth/logout")
async def logout(request: Request):
    """Vide la session."""
    request.session.clear()
    return {"ok": True}


@router.get("/auth/me")
async def me(request: Request):
    """Retourne les infos du user connecté (pour l'UI)."""
    username = request.session.get("username")
    if not username:
        raise HTTPException(status_code=401, detail="Non connecté")
    user = DEMO_USERS.get(username)
    if not user:
        raise HTTPException(status_code=401, detail="Session invalide")
    return {
        "username": username,
        "role": user["role"],
        "region": user["region"],
        "nom_affiche": user["nom_affiche"],
    }
