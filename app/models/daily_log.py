# Modèle journal quotidien — standup numérique par projet
from datetime import date, datetime
from typing import Optional

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class DailyLog(Base):
    """Représente une entrée de journal quotidien pour un projet (standup format)."""

    __tablename__ = "daily_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Projet concerné
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)

    # Utilisateur qui saisit le log
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    log_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Contenu du standup
    what_done: Mapped[str] = mapped_column(Text, nullable=False)
    what_planned: Mapped[str] = mapped_column(Text, nullable=False)
    blockers: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Score d'humeur équipe (1=très mauvais, 5=excellent)
    mood_score: Mapped[int] = mapped_column(Integer, nullable=False, default=3)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)

    # Relations
    project: Mapped["Project"] = relationship("Project", back_populates="daily_logs")
    user: Mapped["User"] = relationship("User", back_populates="daily_logs")

    def __repr__(self) -> str:
        return f"<DailyLog id={self.id} project_id={self.project_id} date={self.log_date}>"
