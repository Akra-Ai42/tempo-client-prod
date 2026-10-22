"""Interface utilisateurs — pointe sur DEMO_USERS de config.py.

Role :
    - Abstraction entre config.py (donnees users) et le reste de l'app
    - Fonctions get_user_by_username() et verify_password() que le reste
      de l'app utilise, sans savoir ou les users sont stockes.
    - Le jour ou on migre vers SQLite / Postgres, on change SEULEMENT
      ce fichier. Les routes auth et le middleware RBAC ne bougent pas.
"""

import bcrypt

from app.config import DEMO_USERS
from app.auth.models import User


def get_user_by_username(username: str) -> User | None:
    """Recupere un utilisateur par son username. None si absent."""
    data = DEMO_USERS.get(username)
    if not data:
        return None
    return User(
        username=username,
        role=data["role"],
        region=data["region"],
        full_name=data["nom_affiche"],
    )


def verify_password(username: str, password: str) -> bool:
    """Verifie qu'un password matche le hash bcrypt stocke."""
    data = DEMO_USERS.get(username)
    if not data:
        # Hash fake pour egaliser le timing (defense contre enumeration)
        bcrypt.checkpw(b"fake", b"$2b$12$" + b"x" * 53)
        return False
    try:
        return bcrypt.checkpw(
            password.encode("utf-8"),
            data["password_hash"],
        )
    except (ValueError, TypeError):
        return False
