# Schémas Pydantic v2 pour les tâches
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


class TaskBase(BaseModel):
    """Champs communs à tous les schémas tâche."""
    model_config = {"from_attributes": True}

    title: str
    description: Optional[str] = None
    status: str = "todo"
    due_date: Optional[date] = None
    is_quick_win: bool = False
    assigned_to_id: Optional[int] = None


class TaskCreate(TaskBase):
    """Schéma de création d'une tâche."""
    project_id: Optional[int] = None


class TaskUpdate(BaseModel):
    """Schéma de mise à jour partielle d'une tâche."""
    model_config = {"from_attributes": True}

    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    due_date: Optional[date] = None
    is_quick_win: Optional[bool] = None
    assigned_to_id: Optional[int] = None
    completed_at: Optional[datetime] = None


class TaskResponse(BaseModel):
    """Schéma de réponse pour une tâche."""
    model_config = {"from_attributes": True}

    id: int
    project_id: int
    assigned_to_id: Optional[int] = None
    title: str
    description: Optional[str] = None
    status: str
    due_date: Optional[date] = None
    completed_at: Optional[datetime] = None
    is_quick_win: bool
    created_at: datetime
    updated_at: datetime
