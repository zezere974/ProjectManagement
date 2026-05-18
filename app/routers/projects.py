# Routeur projets — CRUD, filtres, signalement, journaux quotidiens, export
import csv
import io
import json
import logging
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.alert import Alert
from app.models.daily_log import DailyLog
from app.models.project import Project
from app.models.user import User
from app.routers.auth import get_current_user, require_role
from app.schemas.daily_log import DailyLogCreate, DailyLogResponse
from app.schemas.project import ProjectCreate, ProjectDetail, ProjectResponse, ProjectUpdate
from app.services.alert_service import check_and_create_alerts

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/projects", tags=["Projets"])


@router.get("", response_model=list[ProjectResponse])
async def list_projects(
    status: Optional[str] = Query(None, description="Filtrer par statut"),
    priority: Optional[str] = Query(None, description="Filtrer par priorité"),
    lean_phase: Optional[str] = Query(None, description="Filtrer par phase PDCA"),
    team_id: Optional[int] = Query(None, description="Filtrer par équipe"),
    search: Optional[str] = Query(None, description="Recherche textuelle dans le nom"),
    page: int = Query(1, ge=1, description="Numéro de page"),
    page_size: int = Query(20, ge=1, le=100, description="Taille de page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retourne la liste des projets avec filtres et pagination."""
    query = select(Project).where(Project.is_deleted == False)  # noqa: E712

    if status:
        query = query.where(Project.status == status)
    if priority:
        query = query.where(Project.priority == priority)
    if lean_phase:
        query = query.where(Project.lean_phase == lean_phase)
    if team_id:
        query = query.where(Project.team_id == team_id)
    if search:
        query = query.where(Project.name.ilike(f"%{search}%"))

    # Pagination
    offset = (page - 1) * page_size
    query = query.order_by(Project.updated_at.desc()).offset(offset).limit(page_size)

    projects = db.execute(query).scalars().all()
    return projects


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager"])),
):
    """Crée un nouveau projet. Réservé aux admins et managers."""
    project = Project(**project_data.model_dump())
    if project.owner_id is None:
        project.owner_id = current_user.id

    db.add(project)
    db.commit()
    db.refresh(project)

    # Vérification automatique des alertes
    check_and_create_alerts(db, project)

    logger.info(f"Projet créé : {project.name} (id={project.id}) par {current_user.email}")
    return project


@router.get("/export")
async def export_projects(
    format: str = Query("json", description="Format d'export : csv ou json"),
    status: Optional[str] = Query(None),
    team_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Exporte les projets en CSV ou JSON."""
    query = select(Project).where(Project.is_deleted == False)  # noqa: E712
    if status:
        query = query.where(Project.status == status)
    if team_id:
        query = query.where(Project.team_id == team_id)

    projects = db.execute(query.order_by(Project.name)).scalars().all()

    if format.lower() == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        # En-têtes
        writer.writerow([
            "id", "name", "status", "priority", "lean_phase",
            "progress_pct", "team_id", "owner_id",
            "start_date", "target_date", "actual_end_date",
            "kpi_target", "kpi_actual", "kpi_unit",
            "is_flagged", "created_at", "updated_at",
        ])
        for p in projects:
            writer.writerow([
                p.id, p.name, p.status, p.priority, p.lean_phase,
                p.progress_pct, p.team_id, p.owner_id,
                p.start_date, p.target_date, p.actual_end_date,
                p.kpi_target, p.kpi_actual, p.kpi_unit,
                p.is_flagged, p.created_at, p.updated_at,
            ])
        content = output.getvalue()
        return Response(
            content=content,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=projects.csv"},
        )

    # Format JSON par défaut
    data = [
        {
            "id": p.id,
            "name": p.name,
            "status": p.status,
            "priority": p.priority,
            "lean_phase": p.lean_phase,
            "progress_pct": p.progress_pct,
            "team_id": p.team_id,
            "owner_id": p.owner_id,
            "start_date": str(p.start_date) if p.start_date else None,
            "target_date": str(p.target_date) if p.target_date else None,
            "is_flagged": p.is_flagged,
        }
        for p in projects
    ]
    return Response(
        content=json.dumps(data, ensure_ascii=False, indent=2),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=projects.json"},
    )


@router.get("/{project_id}", response_model=ProjectDetail)
async def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retourne le détail d'un projet avec ses tâches et journaux quotidiens."""
    project = db.execute(
        select(Project).where(Project.id == project_id, Project.is_deleted == False)  # noqa: E712
    ).scalars().first()

    if not project:
        raise HTTPException(status_code=404, detail="Projet introuvable")

    return project


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    project_data: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Met à jour un projet. Admins et managers peuvent modifier tous les projets."""
    project = db.execute(
        select(Project).where(Project.id == project_id, Project.is_deleted == False)  # noqa: E712
    ).scalars().first()

    if not project:
        raise HTTPException(status_code=404, detail="Projet introuvable")

    # Les membres ne peuvent modifier que leurs propres projets
    if current_user.role == "member" and project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Modification non autorisée")

    update_data = project_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)

    db.commit()
    db.refresh(project)

    # Vérification automatique des alertes après mise à jour
    check_and_create_alerts(db, project)

    logger.info(f"Projet mis à jour : {project.name} (id={project.id}) par {current_user.email}")
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager"])),
):
    """Suppression logique d'un projet (is_deleted=True). Réservé aux admins et managers."""
    project = db.execute(
        select(Project).where(Project.id == project_id, Project.is_deleted == False)  # noqa: E712
    ).scalars().first()

    if not project:
        raise HTTPException(status_code=404, detail="Projet introuvable")

    project.is_deleted = True
    db.commit()
    logger.info(f"Projet supprimé (logique) : {project.name} (id={project.id})")


@router.post("/{project_id}/flag", response_model=ProjectResponse)
async def flag_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Signale un projet (is_flagged=True)."""
    project = db.execute(
        select(Project).where(Project.id == project_id, Project.is_deleted == False)  # noqa: E712
    ).scalars().first()

    if not project:
        raise HTTPException(status_code=404, detail="Projet introuvable")

    project.is_flagged = True
    db.commit()
    db.refresh(project)
    logger.info(f"Projet signalé : {project.name} (id={project.id}) par {current_user.email}")
    return project


@router.post("/{project_id}/unflag", response_model=ProjectResponse)
async def unflag_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retire le signalement d'un projet (is_flagged=False)."""
    project = db.execute(
        select(Project).where(Project.id == project_id, Project.is_deleted == False)  # noqa: E712
    ).scalars().first()

    if not project:
        raise HTTPException(status_code=404, detail="Projet introuvable")

    project.is_flagged = False
    db.commit()
    db.refresh(project)
    return project


@router.post("/{project_id}/daily-log", response_model=DailyLogResponse, status_code=status.HTTP_201_CREATED)
async def add_daily_log(
    project_id: int,
    log_data: DailyLogCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Ajoute un journal quotidien (standup) pour un projet."""
    project = db.execute(
        select(Project).where(Project.id == project_id, Project.is_deleted == False)  # noqa: E712
    ).scalars().first()

    if not project:
        raise HTTPException(status_code=404, detail="Projet introuvable")

    daily_log = DailyLog(
        project_id=project_id,
        user_id=current_user.id,
        log_date=log_data.log_date or date.today(),
        what_done=log_data.what_done,
        what_planned=log_data.what_planned,
        blockers=log_data.blockers,
        mood_score=log_data.mood_score,
    )

    db.add(daily_log)
    db.commit()
    db.refresh(daily_log)
    return daily_log
