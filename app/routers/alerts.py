# Routeur alertes — consultation et résolution des alertes
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.alert import Alert
from app.models.user import User
from app.routers.auth import get_current_user
from app.schemas.alert import AlertCreate, AlertResponse
from app.services.alert_service import resolve_alert

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/alerts", tags=["Alertes"])


@router.get("", response_model=list[AlertResponse])
async def get_alerts(
    resolved: Optional[bool] = Query(None, description="Filtrer par statut de résolution"),
    project_id: Optional[int] = Query(None, description="Filtrer par projet"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retourne la liste des alertes avec filtres optionnels."""
    query = select(Alert).order_by(Alert.created_at.desc())

    if resolved is not None:
        query = query.where(Alert.is_resolved == resolved)
    if project_id is not None:
        query = query.where(Alert.project_id == project_id)

    alerts = db.execute(query).scalars().all()
    return alerts


@router.post("", response_model=AlertResponse, status_code=201)
async def create_alert(
    alert_data: AlertCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Crée une alerte manuellement sur un projet."""
    from app.models.project import Project
    project = db.execute(
        select(Project).where(Project.id == alert_data.project_id, Project.is_deleted == False)  # noqa: E712
    ).scalars().first()

    if not project:
        raise HTTPException(status_code=404, detail="Projet introuvable")

    alert = Alert(
        project_id=alert_data.project_id,
        created_by_id=current_user.id,
        type=alert_data.type,
        message=alert_data.message,
        is_resolved=False,
        teams_notified=False,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)

    logger.info(f"Alerte créée : type={alert.type} projet={alert.project_id} par {current_user.email}")
    return alert


@router.put("/{alert_id}/resolve", response_model=AlertResponse)
async def resolve_alert_route(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Marque une alerte comme résolue."""
    try:
        alert = resolve_alert(db, alert_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    logger.info(f"Alerte résolue : id={alert_id} par {current_user.email}")
    return alert
