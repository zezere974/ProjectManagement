# Service KPI — calcul des indicateurs de performance pour les équipes et le tableau de bord
from datetime import date
from typing import Any, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.daily_log import DailyLog
from app.models.alert import Alert


def get_team_kpis(db: Session, team_id: Optional[int] = None) -> dict[str, Any]:
    """
    Calcule les KPIs pour une équipe ou toutes les équipes.
    Retourne : taux de livraison dans les délais, vélocité, humeur moyenne.
    """
    # Filtre par équipe si spécifié
    query = select(Project).where(Project.is_deleted == False)  # noqa: E712
    if team_id is not None:
        query = query.where(Project.team_id == team_id)

    projects = db.execute(query).scalars().all()

    if not projects:
        return {
            "team_id": team_id,
            "total_projects": 0,
            "active_projects": 0,
            "blocked_projects": 0,
            "done_projects": 0,
            "on_time_rate": 0.0,
            "avg_progress": 0.0,
            "avg_mood": 0.0,
            "velocity": 0,
        }

    total = len(projects)
    active = sum(1 for p in projects if p.status == "in_progress")
    blocked = sum(1 for p in projects if p.status == "blocked")
    done = sum(1 for p in projects if p.status == "done")

    # Taux de livraison dans les délais : projets terminés avant ou à la date cible
    done_projects = [p for p in projects if p.status == "done"]
    on_time_done = sum(
        1 for p in done_projects
        if p.target_date is not None
        and p.actual_end_date is not None
        and p.actual_end_date <= p.target_date
    )
    on_time_rate = (on_time_done / len(done_projects) * 100) if done_projects else 0.0

    # Progression moyenne
    avg_progress = sum(p.progress_pct for p in projects) / total

    # Humeur moyenne (journaux des 7 derniers jours)
    from datetime import timedelta
    seven_days_ago = date.today() - timedelta(days=7)
    mood_query = select(func.avg(DailyLog.mood_score)).where(
        DailyLog.log_date >= seven_days_ago
    )
    if team_id is not None:
        project_ids = [p.id for p in projects]
        mood_query = mood_query.where(DailyLog.project_id.in_(project_ids))

    avg_mood_result = db.execute(mood_query).scalar()
    avg_mood = float(avg_mood_result) if avg_mood_result is not None else 0.0

    # Vélocité : nombre de tâches terminées cette semaine
    from app.models.task import Task
    velocity_query = select(func.count(Task.id)).where(
        Task.status == "done",
        Task.updated_at >= date.today().replace(day=date.today().day - date.today().weekday()),
    )
    velocity = db.execute(velocity_query).scalar() or 0

    return {
        "team_id": team_id,
        "total_projects": total,
        "active_projects": active,
        "blocked_projects": blocked,
        "done_projects": done,
        "on_time_rate": round(on_time_rate, 1),
        "avg_progress": round(avg_progress, 1),
        "avg_mood": round(avg_mood, 2),
        "velocity": velocity,
    }


def get_global_kpis(db: Session) -> dict[str, Any]:
    """
    Calcule les KPIs globaux pour le tableau de bord principal.
    """
    projects = db.execute(
        select(Project).where(Project.is_deleted == False)  # noqa: E712
    ).scalars().all()

    total = len(projects)
    if total == 0:
        return {
            "total_projects": 0,
            "active_projects": 0,
            "blocked_projects": 0,
            "done_projects": 0,
            "flagged_projects": 0,
            "avg_mood": 0.0,
            "avg_progress": 0.0,
            "on_time_rate": 0.0,
            "total_alerts": 0,
            "unresolved_alerts": 0,
        }

    active = sum(1 for p in projects if p.status == "in_progress")
    blocked = sum(1 for p in projects if p.status == "blocked")
    done = sum(1 for p in projects if p.status == "done")
    flagged = sum(1 for p in projects if p.is_flagged)

    # Taux de livraison dans les délais
    done_projects = [p for p in projects if p.status == "done"]
    on_time = sum(
        1 for p in done_projects
        if p.target_date is not None
        and p.actual_end_date is not None
        and p.actual_end_date <= p.target_date
    )
    on_time_rate = (on_time / len(done_projects) * 100) if done_projects else 0.0

    # Progression moyenne
    avg_progress = sum(p.progress_pct for p in projects) / total

    # Humeur moyenne (7 derniers jours)
    from datetime import timedelta
    seven_days_ago = date.today() - timedelta(days=7)
    avg_mood_result = db.execute(
        select(func.avg(DailyLog.mood_score)).where(DailyLog.log_date >= seven_days_ago)
    ).scalar()
    avg_mood = float(avg_mood_result) if avg_mood_result is not None else 0.0

    # Alertes
    total_alerts = db.execute(select(func.count(Alert.id))).scalar() or 0
    unresolved_alerts = db.execute(
        select(func.count(Alert.id)).where(Alert.is_resolved == False)  # noqa: E712
    ).scalar() or 0

    return {
        "total_projects": total,
        "active_projects": active,
        "blocked_projects": blocked,
        "done_projects": done,
        "flagged_projects": flagged,
        "avg_mood": round(avg_mood, 2),
        "avg_progress": round(avg_progress, 1),
        "on_time_rate": round(on_time_rate, 1),
        "total_alerts": total_alerts,
        "unresolved_alerts": unresolved_alerts,
    }
