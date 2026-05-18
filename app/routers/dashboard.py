# Routeur tableau de bord — KPIs globaux, alertes et distribution PDCA
import logging

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.alert import Alert
from app.models.project import Project
from app.models.user import User
from app.routers.auth import get_current_user
from app.schemas.dashboard import DashboardKPI, DashboardResponse
from app.services.kpi_service import get_global_kpis
from app.services.pdca_service import get_pdca_distribution

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Tableau de bord"])


@router.get("/api/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retourne les données complètes du tableau de bord :
    - KPIs globaux
    - Alertes actives
    - Projets signalés
    - Top 3 projets critiques
    - Distribution PDCA
    - Humeur de l'équipe
    """
    # KPIs globaux
    kpi_data = get_global_kpis(db)
    kpis = DashboardKPI(**kpi_data)

    # Alertes actives (non résolues)
    active_alerts = db.execute(
        select(Alert)
        .where(Alert.is_resolved == False)  # noqa: E712
        .order_by(Alert.created_at.desc())
        .limit(10)
    ).scalars().all()

    # Projets signalés
    flagged_projects = db.execute(
        select(Project)
        .where(Project.is_flagged == True, Project.is_deleted == False)  # noqa: E712
        .order_by(Project.updated_at.desc())
        .limit(5)
    ).scalars().all()

    # Top 3 projets critiques (bloqués ou priorité critique)
    critical_projects = db.execute(
        select(Project)
        .where(
            Project.is_deleted == False,  # noqa: E712
            Project.status.in_(["blocked", "in_progress"]),
            Project.priority == "critical",
        )
        .order_by(Project.updated_at.desc())
        .limit(3)
    ).scalars().all()

    # Distribution PDCA
    pdca_dist = get_pdca_distribution(db)

    # Humeur de l'équipe (par équipe)
    from datetime import date, timedelta
    from sqlalchemy import func
    from app.models.daily_log import DailyLog
    from app.models.team import Team

    seven_days_ago = date.today() - timedelta(days=7)
    team_mood_raw = db.execute(
        select(Team.id, Team.name, func.avg(DailyLog.mood_score).label("avg_mood"))
        .join(Project, Project.team_id == Team.id)
        .join(DailyLog, DailyLog.project_id == Project.id)
        .where(DailyLog.log_date >= seven_days_ago)
        .group_by(Team.id, Team.name)
    ).all()

    team_mood = {
        row.name: round(float(row.avg_mood), 2)
        for row in team_mood_raw
        if row.avg_mood is not None
    }

    return DashboardResponse(
        kpis=kpis,
        active_alerts=active_alerts,
        flagged_projects=flagged_projects,
        critical_projects=critical_projects,
        pdca_distribution=pdca_dist,
        team_mood=team_mood,
    )
