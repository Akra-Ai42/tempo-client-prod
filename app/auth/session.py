"""Helpers de gestion de session Tempo Client."""

from fastapi import HTTPException, Request, status

from app.auth.models import User
from app.auth.users import get_user_by_username


SESSION_KEY = "user"


def login_user(request: Request, user: User) -> None:
    """Pose l'identite dans la session cookie signee."""
    request.session[SESSION_KEY] = user.username


def logout_user(request: Request) -> None:
    """Supprime l'identite de la session (deconnexion)."""
    request.session.pop(SESSION_KEY, None)


def get_current_user(request: Request) -> User:
    """Recupere l'utilisateur courant depuis la session.

    Dependency injection FastAPI :
        async def mon_endpoint(user: User = Depends(get_current_user)):
            ...
    """
    username = request.session.get(SESSION_KEY)
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Non authentifie",
        )

    user = get_user_by_username(username)
    if not user:
        request.session.pop(SESSION_KEY, None)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session invalide",
        )

    return user


def get_current_user_optional(request: Request) -> User | None:
    """Variante qui retourne None au lieu de lever une exception."""
    try:
        return get_current_user(request)
    except HTTPException:
        return None
