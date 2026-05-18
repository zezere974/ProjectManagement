# Schémas Pydantic v2 pour les utilisateurs et l'authentification
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator


class UserBase(BaseModel):
    """Champs communs à tous les schémas utilisateur."""
    model_config = model_config = {"from_attributes": True}

    email: str
    username: str
    role: str = "member"
    is_active: bool = True


class UserCreate(BaseModel):
    """Schéma de création d'un utilisateur (avec mot de passe)."""
    model_config = {"from_attributes": True}

    email: str
    username: str
    password: str
    role: str = "member"
    is_active: bool = True

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        allowed = {"admin", "manager", "member"}
        if v not in allowed:
            raise ValueError(f"Le rôle doit être l'un de : {allowed}")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Le mot de passe doit contenir au moins 8 caractères")
        return v


class UserUpdate(BaseModel):
    """Schéma de mise à jour partielle d'un utilisateur."""
    model_config = {"from_attributes": True}

    email: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    teams_user_id: Optional[str] = None


class UserResponse(BaseModel):
    """Schéma de réponse utilisateur (sans mot de passe)."""
    model_config = {"from_attributes": True}

    id: int
    email: str
    username: str
    role: str
    is_active: bool
    last_login: Optional[datetime] = None
    sso_provider: Optional[str] = None
    teams_user_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class Token(BaseModel):
    """Réponse de token JWT."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Données encodées dans le token JWT."""
    user_id: Optional[int] = None
    email: Optional[str] = None
    role: Optional[str] = None
