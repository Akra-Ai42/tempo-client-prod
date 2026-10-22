"""Endpoints FastAPI pour l'authentification Tempo Client."""

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.auth.models import (
    LoginRequest,
    LoginResponse,
    LogoutResponse,
    MeResponse,
    User,
)
from app.auth.session import (
    get_current_user,
    login_user,
    logout_user,
)
from app.auth.users import get_user_by_username, verify_password


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
async def login(payload: LoginRequest, request: Request) -> LoginResponse:
    """Authentifie un utilisateur et pose un cookie de session."""
    user = get_user_by_username(payload.username)
    if not user or not verify_password(payload.username, payload.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiants invalides",
        )

    login_user(request, user)

    return LoginResponse(
        username=user.username,
        role=user.role,
        region=user.region,
        full_name=user.full_name,
    )


@router.post("/logout", response_model=LogoutResponse)
async def logout(request: Request) -> LogoutResponse:
    """Deconnecte l'utilisateur en vidant la session."""
    logout_user(request)
    return LogoutResponse()


@router.get("/me", response_model=MeResponse)
async def me(user: User = Depends(get_current_user)) -> MeResponse:
    """Retourne l'identite de l'utilisateur courant."""
    return MeResponse(
        username=user.username,
        role=user.role,
        region=user.region,
        full_name=user.full_name,
    )
