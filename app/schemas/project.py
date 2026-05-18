# Schémas Pydantic v2 pour les projets
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, field_validator

from app.schemas.task import TaskResponse
from app.schemas.daily_log import DailyLogResponse


class ProjectBase(BaseModel):
    """Champs communs à tous les schémas projet."""
    model_config = {"from_attributes": True}

    name: str
    description: Optional[str] = None
    team_id: Optional[int] = None
    status: str = "backlog"
    priority: str = "medium"
    lean_phase: str = "plan"
    owner_id: Optional[int] = None
    start_date: Optional[date] = None
    target_date: Optional[date] = None
    actual_end_date: Optional[date] = None
    progress_pct: int = 0
    kpi_target: Optional[float] = None
    kpi_actual: Optional[float] = None
    kpi_unit: Optional[str] = None
    is_flagged: bool = False
    notes: Optional[str] = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        allowed = {"backlog", "in_progress", "blocked", "done", "cancelled"}
        if v not in allowed:
            raise ValueError(f"Le statut doit être l'un de : {allowed}")
        return v

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: str) -> str:
        allowed = {"low", "medium", "high", "critical"}
        if v not in allowed:
            raise ValueError(f"La priorité doit être l'une de : {allowed}")
        return v

    @field_validator("lean_phase")
    @classmethod
    def validate_lean_phase(cls, v: str) -> str:
        allowed = {"plan", "do", "check", "act"}
        if v not in allowed:
            raise ValueError(f"La phase PDCA doit être l'une de : {allowed}")
        return v

    @field_validator("progress_pct")
    @classmethod
    def validate_progress(cls, v: int) -> int:
        if not 0 <= v <= 100:
            raise ValueError("La progression doit être entre 0 et 100")
        return v


class ProjectCreate(ProjectBase):
    """Schéma de création d'un projet."""
    pass


class ProjectUpdate(BaseModel):
    """Schéma de mise à jour partielle d'un projet."""
    model_config = {"from_attributes": True}

    name: Optional[str] = None
    description: Optional[str] = None
    team_id: Optional[int] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    lean_phase: Optional[str] = None
    owner_id: Optional[int] = None
    start_date: Optional[date] = None
    target_date: Optional[date] = None
    actual_end_date: Optional[date] = None
    progress_pct: Optional[int] = None
    kpi_target: Optional[float] = None
    kpi_actual: Optional[float] = None
    kpi_unit: Optional[str] = None
    is_flagged: Optional[bool] = None
    notes: Optional[str] = None


class ProjectResponse(BaseModel):
    """Schéma de réponse pour un projet (liste)."""
    model_config = {"from_attributes": True}

    id: int
    name: str
    description: Optional[str] = None
    team_id: Optional[int] = None
    status: str
    priority: str
    lean_phase: str
    owner_id: Optional[int] = None
    start_date: Optional[date] = None
    target_date: Optional[date] = None
    actual_end_date: Optional[date] = None
    progress_pct: int
    kpi_target: Optional[float] = None
    kpi_actual: Optional[float] = None
    kpi_unit: Optional[str] = None
    is_flagged: bool
    notes: Optional[str] = None
    is_deleted: bool
    created_at: datetime
    updated_at: datetime


class ProjectDetail(ProjectResponse):
    """Schéma de réponse détaillé pour un projet (avec tâches et journaux)."""
    tasks: list[TaskResponse] = []
    daily_logs: list[DailyLogResponse] = []
