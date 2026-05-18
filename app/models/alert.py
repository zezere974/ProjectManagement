# Modèle alerte — signalement des risques et blocages sur les projets
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Alert(Base):
    """Représente une alerte créée sur un projet (blocage, retard, escalade, etc.)."""

    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Projet concerné
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)

    # Utilisateur créateur de l'alerte
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    # Type: delay | blocker | quality | resource | escalation
    type: Mapped[str] = mapped_column(String(20), nullable=False)

    message: Mapped[str] = mapped_column(Text, nullable=False)

    # Résolution
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    resolved_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)

    # Notification Teams (Phase 3)
    teams_notified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relations
    project: Mapped["Project"] = relationship("Project", back_populates="alerts")
    created_by: Mapped["User"] = relationship(
        "User", back_populates="created_alerts", foreign_keys=[created_by_id]
    )
    resolved_by: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[resolved_by_id]
    )

    def __repr__(self) -> str:
        return f"<Alert id={self.id} type={self.type} resolved={self.is_resolved}>"
