# Routeur HTMX — endpoints retournant du HTML pour les interactions UI
from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.alert import Alert
from app.models.daily_log import DailyLog
from app.models.project import Project
from app.models.task import Task
from app.models.user import User
from app.routers.auth import get_current_user

router = APIRouter(prefix="/htmx", tags=["HTMX"])
templates = Jinja2Templates(directory="app/templates")


@router.post("/projects/{project_id}/tasks")
async def htmx_create_task(
    request: Request,
    project_id: int,
    title: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Crée une tâche et retourne le HTML de la ligne de tâche."""
    project = db.execute(
        select(Project).where(Project.id == project_id, Project.is_deleted == False)  # noqa: E712
    ).scalars().first()
    if not project:
        raise HTTPException(404, "Projet introuvable")

    task = Task(project_id=project_id, title=title.strip(), status="todo")
    db.add(task)
    db.commit()
    db.refresh(task)

    return templates.TemplateResponse(
        request, "partials/task_item.html", {"task": task, "current_user": current_user}
    )


@router.post("/tasks/{task_id}/toggle")
async def htmx_toggle_task(
    request: Request,
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Bascule l'état fait/non-fait d'une tâche et retourne le HTML mis à jour."""
    task = db.execute(select(Task).where(Task.id == task_id)).scalars().first()
    if not task:
        raise HTTPException(404, "Tâche introuvable")

    task.status = "todo" if task.status == "done" else "done"
    task.completed_at = datetime.utcnow() if task.status == "done" else None
    db.commit()
    db.refresh(task)

    return templates.TemplateResponse(
        request, "partials/task_item.html", {"task": task, "current_user": current_user}
    )


@router.delete("/tasks/{task_id}")
async def htmx_delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Supprime une tâche et retourne une réponse vide (HTMX retire l'élément)."""
    task = db.execute(select(Task).where(Task.id == task_id)).scalars().first()
    if not task:
        raise HTTPException(404, "Tâche introuvable")
    db.delete(task)
    db.commit()
    return Response(content="", status_code=200)


@router.post("/projects/{project_id}/update")
async def htmx_update_project(
    request: Request,
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Met à jour un ou plusieurs champs projet depuis un formulaire HTMX."""
    project = db.execute(
        select(Project).where(Project.id == project_id, Project.is_deleted == False)  # noqa: E712
    ).scalars().first()
    if not project:
        raise HTTPException(404, "Projet introuvable")

    form = await request.form()
    allowed = {"status", "lean_phase", "progress_pct", "priority"}

    for field in allowed:
        if field in form and form[field]:
            val = form[field]
            if field == "progress_pct":
                val = int(val)
            setattr(project, field, val)

    db.commit()

    return Response(
        content=(
            '<span class="inline-flex items-center gap-1 text-emerald-600 text-xs font-semibold">'
            '<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">'
            '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7"/>'
            "</svg>Sauvegardé</span>"
        ),
        media_type="text/html",
        status_code=200,
    )


@router.post("/alerts/{alert_id}/resolve")
async def htmx_resolve_alert(
    request: Request,
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Résout une alerte et retourne le HTML mis à jour."""
    alert = db.execute(select(Alert).where(Alert.id == alert_id)).scalars().first()
    if not alert:
        raise HTTPException(404, "Alerte introuvable")

    alert.is_resolved = True
    alert.resolved_at = datetime.utcnow()
    alert.resolved_by_id = current_user.id
    db.commit()
    db.refresh(alert)

    return templates.TemplateResponse(
        request, "partials/alert_item.html", {"alert": alert, "current_user": current_user}
    )


@router.post("/projects/{project_id}/daily-log")
async def htmx_daily_log(
    request: Request,
    project_id: int,
    what_done: str = Form(...),
    what_planned: str = Form(...),
    blockers: Optional[str] = Form(None),
    mood_score: int = Form(3),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Enregistre ou met à jour le log standup du jour."""
    today = date.today()

    existing = db.execute(
        select(DailyLog).where(
            DailyLog.project_id == project_id,
            DailyLog.user_id == current_user.id,
            DailyLog.log_date == today,
        )
    ).scalars().first()

    if existing:
        existing.what_done = what_done
        existing.what_planned = what_planned
        existing.blockers = blockers or None
        existing.mood_score = mood_score
    else:
        log = DailyLog(
            project_id=project_id,
            user_id=current_user.id,
            log_date=today,
            what_done=what_done,
            what_planned=what_planned,
            blockers=blockers or None,
            mood_score=mood_score,
        )
        db.add(log)

    db.commit()

    return Response(
        content=(
            '<div class="flex items-center gap-2 text-emerald-600 text-sm font-medium py-1">'
            '<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">'
            '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" '
            'd="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>'
            "Standup enregistré ✓</div>"
        ),
        media_type="text/html",
        status_code=200,
    )
