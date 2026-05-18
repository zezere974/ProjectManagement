# Modèle projet — gestion des projets IIoT/OT avec phases PDCA et métriques Lean
from datetime import date, datetime
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Project(Base):
    """Représente un projet industriel/IIoT avec suivi Lean et PDCA."""

    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Équipe responsable
    team_id: Mapped[Optional[int]] = mapped_column(ForeignKey("teams.id"), nullable=True)

    # Statut: backlog | in_progress | blocked | done | cancelled
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="backlog")

    # Priorité: low | medium | high | critical
    priority: Mapped[str] = mapped_column(String(20), nullable=False, default="medium")

    # Phase PDCA: plan | do | check | act
    lean_phase: Mapped[str] = mapped_column(String(10), nullable=False, default="plan")

    # Propriétaire du projet
    owner_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)

    # Dates
    start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    target_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    actual_end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Avancement
    progress_pct: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # KPIs
    kpi_target: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    kpi_actual: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    kpi_unit: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Signalement et notes
    is_flagged: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Suppression logique
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relations
    team: Mapped[Optional["Team"]] = relationship("Team", back_populates="projects")
    owner: Mapped[Optional["User"]] = relationship(
        "User", back_populates="owned_projects", foreign_keys=[owner_id]
    )
    tasks: Mapped[list["Task"]] = relationship(
        "Task", back_populates="project", cascade="all, delete-orphan"
    )
    daily_logs: Mapped[list["DailyLog"]] = relationship(
        "DailyLog", back_populates="project", cascade="all, delete-orphan"
    )
    alerts: Mapped[list["Alert"]] = relationship(
        "Alert", back_populates="project", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Project id={self.id} name={self.name} status={self.status}>"
