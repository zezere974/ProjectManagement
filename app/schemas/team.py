# Schémas Pydantic v2 pour les équipes
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class TeamBase(BaseModel):
    """Champs communs à tous les schémas équipe."""
    model_config = {"from_attributes": True}

    name: str
    description: Optional[str] = None
    manager_id: Optional[int] = None
    color_code: str = "#6b7280"
    teams_channel_id: Optional[str] = None
    teams_webhook_url: Optional[str] = None


class TeamCreate(TeamBase):
    """Schéma de création d'une équipe."""
    pass


class TeamUpdate(BaseModel):
    """Schéma de mise à jour partielle d'une équipe."""
    model_config = {"from_attributes": True}

    name: Optional[str] = None
    description: Optional[str] = None
    manager_id: Optional[int] = None
    color_code: Optional[str] = None
    teams_channel_id: Optional[str] = None
    teams_webhook_url: Optional[str] = None


class TeamResponse(BaseModel):
    """Schéma de réponse pour une équipe."""
    model_config = {"from_attributes": True}

    id: int
    name: str
    description: Optional[str] = None
    manager_id: Optional[int] = None
    color_code: str
    teams_channel_id: Optional[str] = None
    teams_webhook_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
