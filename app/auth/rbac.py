"""Controle d'acces base sur les roles (RBAC) via dependances FastAPI.

Pattern :
    - Chaque endpoint protege declare ses exigences via Depends()
    - require_role("direction") -> l'user doit avoir ce role, sinon 403
    - filter_clients_by_user() -> filtre la liste des clients selon le role

Role vs region :
    - role "direction"   : voit tous les clients, toutes regions
    - role "conseiller"  : voit uniquement les clients de SA region
"""

from fastapi import Depends, HTTPException, status

from app.auth.models import User
from app.auth.session import get_current_user


def require_role(required_role: str):
    """Fabrique une dependance FastAPI qui exige un role precis.

    Usage :
        @router.get("/dashboard")
        async def dashboard(user: User = Depends(require_role("direction"))):
            ...
    """
    async def _check(user: User = Depends(get_current_user)) -> User:
        if user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acces reserve au role '{required_role}'",
            )
        return user
    return _check


def require_conseiller(user: User = Depends(get_current_user)) -> User:
    """Dependance : exige role 'conseiller'."""
    if user.role != "conseiller":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acces reserve aux conseillers",
        )
    return user


def require_direction(user: User = Depends(get_current_user)) -> User:
    """Dependance : exige role 'direction'."""
    if user.role != "direction":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acces reserve a la direction",
        )
    return user


def filter_clients_by_user(clients: list[dict], user: User) -> list[dict]:
    """Filtre la liste des clients selon le role et la region de l'user.

    Regles metier :
        - Direction : voit tous les clients, toutes regions
        - Conseiller : voit uniquement les clients de sa region

    Args:
        clients: liste complete des clients (dicts avec cle "region")
        user: user courant depuis la session

    Returns:
        Liste filtree selon les droits de l'user.
    """
    if user.role == "direction":
        return clients

    return [c for c in clients if c["region"] == user.region]
