# Modèle export de rapport — squelette Phase 2
from datetime import date, datetime
from typing import Optional

from sqlalchemy import Date, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ReportExport(Base):
    """Représente un export de rapport généré (disponible en Phase 2)."""

    __tablename__ = "report_exports"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Utilisateur ayant généré le rapport
    generated_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    # Type: weekly | monthly | project | team_kpi
    report_type: Mapped[str] = mapped_column(String(20), nullable=False)

    # Format: excel | pdf | pptx
    format: Mapped[str] = mapped_column(String(10), nullable=False)

    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)

    # Chemin du fichier généré (null si pas encore généré)
    file_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)

    # Relations
    generated_by: Mapped["User"] = relationship("User", foreign_keys=[generated_by_id])

    def __repr__(self) -> str:
        return f"<ReportExport id={self.id} type={self.report_type} format={self.format}>"
