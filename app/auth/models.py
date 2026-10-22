"""Modeles Pydantic pour l'authentification Tempo Client."""

from dataclasses import dataclass
from typing import Optional

from pydantic import BaseModel, Field


@dataclass(frozen=True)
class User:
    """Representation interne d'un utilisateur."""
    username: str
    role: str              # "conseiller" ou "direction"
    region: Optional[str]  # "lille" ou "marseille" pour conseillers, None pour direction
    full_name: str


class LoginRequest(BaseModel):
    """Payload POST /auth/login."""
    username: str = Field(..., min_length=1, max_length=64)
    password: str = Field(..., min_length=1, max_length=256)


class LoginResponse(BaseModel):
    username: str
    role: str
    region: Optional[str]
    full_name: str
    message: str = "Login reussi"


class MeResponse(BaseModel):
    username: str
    role: str
    region: Optional[str]
    full_name: str


class LogoutResponse(BaseModel):
    message: str = "Deconnecte"
