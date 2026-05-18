# Modèle équipe — groupes de travail avec manager et canal Teams
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Team(Base):
    """Représente une équipe de travail."""

    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Responsable de l'équipe
    manager_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )

    # Code couleur hexadécimal pour l'affichage visuel lean
    color_code: Mapped[str] = mapped_column(String(7), nullable=False, default="#6b7280")

    # Intégration Teams (Phase 3)
    teams_channel_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    teams_webhook_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relations
    manager: Mapped[Optional["User"]] = relationship(
        "User", back_populates="managed_teams", foreign_keys=[manager_id]
    )
    projects: Mapped[list["Project"]] = relationship(
        "Project", back_populates="team"
    )

    def __repr__(self) -> str:
        return f"<Team id={self.id} name={self.name}>"
