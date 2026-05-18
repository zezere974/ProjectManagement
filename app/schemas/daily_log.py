# Schémas Pydantic v2 pour les journaux quotidiens
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, field_validator


class DailyLogBase(BaseModel):
    """Champs communs à tous les schémas journal quotidien."""
    model_config = {"from_attributes": True}

    log_date: date
    what_done: str
    what_planned: str
    blockers: Optional[str] = None
    mood_score: int = 3

    @field_validator("mood_score")
    @classmethod
    def validate_mood(cls, v: int) -> int:
        if not 1 <= v <= 5:
            raise ValueError("Le score d'humeur doit être entre 1 et 5")
        return v


class DailyLogCreate(DailyLogBase):
    """Schéma de création d'un journal quotidien."""
    project_id: Optional[int] = None
    user_id: Optional[int] = None


class DailyLogResponse(BaseModel):
    """Schéma de réponse pour un journal quotidien."""
    model_config = {"from_attributes": True}

    id: int
    project_id: int
    user_id: int
    log_date: date
    what_done: str
    what_planned: str
    blockers: Optional[str] = None
    mood_score: int
    created_at: datetime
