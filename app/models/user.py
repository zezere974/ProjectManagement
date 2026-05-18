# Modèle utilisateur — authentification et gestion des rôles
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    """Représente un utilisateur de l'application."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    hashed_password: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Rôle: admin | manager | member
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="member")

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Champs SSO (Phase 2)
    sso_provider: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    sso_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Intégration Teams (Phase 3)
    teams_user_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relations
    managed_teams: Mapped[list["Team"]] = relationship(
        "Team", back_populates="manager", foreign_keys="Team.manager_id"
    )
    owned_projects: Mapped[list["Project"]] = relationship(
        "Project", back_populates="owner", foreign_keys="Project.owner_id"
    )
    tasks: Mapped[list["Task"]] = relationship(
        "Task", back_populates="assigned_to", foreign_keys="Task.assigned_to_id"
    )
    daily_logs: Mapped[list["DailyLog"]] = relationship(
        "DailyLog", back_populates="user"
    )
    created_alerts: Mapped[list["Alert"]] = relationship(
        "Alert", back_populates="created_by", foreign_keys="Alert.created_by_id"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email} role={self.role}>"
