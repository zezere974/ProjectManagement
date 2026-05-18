# Schémas Pydantic v2 pour les alertes
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator


class AlertBase(BaseModel):
    """Champs communs à tous les schémas alerte."""
    model_config = {"from_attributes": True}

    type: str
    message: str

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        allowed = {"delay", "blocker", "quality", "resource", "escalation"}
        if v not in allowed:
            raise ValueError(f"Le type doit être l'un de : {allowed}")
        return v


class AlertCreate(AlertBase):
    """Schéma de création d'une alerte."""
    project_id: int


class AlertResponse(BaseModel):
    """Schéma de réponse pour une alerte."""
    model_config = {"from_attributes": True}

    id: int
    project_id: int
    created_by_id: int
    type: str
    message: str
    is_resolved: bool
    resolved_at: Optional[datetime] = None
    resolved_by_id: Optional[int] = None
    teams_notified: bool
    created_at: datetime
    updated_at: datetime
