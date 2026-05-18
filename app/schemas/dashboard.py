# Schémas Pydantic v2 pour le tableau de bord
from typing import Any, Optional

from pydantic import BaseModel

from app.schemas.alert import AlertResponse
from app.schemas.project import ProjectResponse


class DashboardKPI(BaseModel):
    """Indicateurs clés de performance pour le tableau de bord."""
    model_config = {"from_attributes": True}

    total_projects: int = 0
    active_projects: int = 0
    blocked_projects: int = 0
    done_projects: int = 0
    flagged_projects: int = 0
    avg_mood: float = 0.0
    avg_progress: float = 0.0
    on_time_rate: float = 0.0
    total_alerts: int = 0
    unresolved_alerts: int = 0


class DashboardResponse(BaseModel):
    """Réponse complète du tableau de bord."""
    model_config = {"from_attributes": True}

    kpis: DashboardKPI
    active_alerts: list[AlertResponse] = []
    flagged_projects: list[ProjectResponse] = []
    critical_projects: list[ProjectResponse] = []
    pdca_distribution: dict[str, int] = {}
    team_mood: dict[str, Any] = {}
