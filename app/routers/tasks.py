# Routeur tâches — gestion des tâches par projet
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.project import Project
from app.models.task import Task
from app.models.user import User
from app.routers.auth import get_current_user
from app.schemas.task import TaskCreate, TaskResponse, TaskUpdate

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Tâches"])


@router.get("/api/projects/{project_id}/tasks", response_model=list[TaskResponse])
async def get_project_tasks(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retourne toutes les tâches d'un projet."""
    project = db.execute(
        select(Project).where(Project.id == project_id, Project.is_deleted == False)  # noqa: E712
    ).scalars().first()

    if not project:
        raise HTTPException(status_code=404, detail="Projet introuvable")

    tasks = db.execute(
        select(Task)
        .where(Task.project_id == project_id)
        .order_by(Task.created_at)
    ).scalars().all()

    return tasks


@router.post("/api/projects/{project_id}/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    project_id: int,
    task_data: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Crée une nouvelle tâche pour un projet."""
    project = db.execute(
        select(Project).where(Project.id == project_id, Project.is_deleted == False)  # noqa: E712
    ).scalars().first()

    if not project:
        raise HTTPException(status_code=404, detail="Projet introuvable")

    task_dict = task_data.model_dump(exclude={"project_id"})
    task = Task(project_id=project_id, **task_dict)

    db.add(task)
    db.commit()
    db.refresh(task)

    logger.info(f"Tâche créée : {task.title} (projet={project_id}) par {current_user.email}")
    return task


@router.put("/api/tasks/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    task_data: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Met à jour une tâche."""
    task = db.execute(select(Task).where(Task.id == task_id)).scalars().first()

    if not task:
        raise HTTPException(status_code=404, detail="Tâche introuvable")

    update_data = task_data.model_dump(exclude_unset=True)

    # Si on marque la tâche comme terminée, enregistrer la date de complétion
    if update_data.get("status") == "done" and task.status != "done":
        update_data["completed_at"] = datetime.utcnow()
    elif update_data.get("status") and update_data["status"] != "done":
        update_data["completed_at"] = None

    for field, value in update_data.items():
        setattr(task, field, value)

    db.commit()
    db.refresh(task)
    return task


@router.delete("/api/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Supprime une tâche définitivement."""
    task = db.execute(select(Task).where(Task.id == task_id)).scalars().first()

    if not task:
        raise HTTPException(status_code=404, detail="Tâche introuvable")

    db.delete(task)
    db.commit()
    logger.info(f"Tâche supprimée : id={task_id} par {current_user.email}")
