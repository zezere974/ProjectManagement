# Modèle tâche — actions unitaires liées aux projets
from datetime import date, datetime
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Task(Base):
    """Représente une tâche liée à un projet."""

    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Projet parent
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)

    # Responsable de la tâche
    assigned_to_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)

    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Statut: todo | in_progress | done | blocked
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="todo")

    due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Quick win — tâche à fort impact rapide
    is_quick_win: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relations
    project: Mapped["Project"] = relationship("Project", back_populates="tasks")
    assigned_to: Mapped[Optional["User"]] = relationship(
        "User", back_populates="tasks", foreign_keys=[assigned_to_id]
    )

    def __repr__(self) -> str:
        return f"<Task id={self.id} title={self.title} status={self.status}>"
