# Service PDCA — suggestions de phase et distribution des projets
from typing import TYPE_CHECKING, Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

if TYPE_CHECKING:
    from app.models.project import Project


# Séquence PDCA standard
PDCA_SEQUENCE = ["plan", "do", "check", "act"]

# Seuils de progression pour avancer dans le cycle PDCA
PDCA_PROGRESS_THRESHOLDS = {
    "plan": 25,   # Passer à DO à partir de 25% de progression
    "do": 70,     # Passer à CHECK à partir de 70%
    "check": 90,  # Passer à ACT à partir de 90%
    "act": 100,   # Terminé
}


def suggest_next_phase(project: "Project") -> str:
    """
    Suggère la prochaine phase PDCA en fonction de la progression et du statut du projet.
    Retourne la phase suggérée (plan | do | check | act).
    """
    current_phase = project.lean_phase
    progress = project.progress_pct
    status = project.status

    # Projet terminé — rester en ACT
    if status == "done":
        return "act"

    # Projet bloqué — rester dans la phase actuelle
    if status == "blocked":
        return current_phase

    # Projet annulé — ne pas suggérer de progression
    if status == "cancelled":
        return current_phase

    # Vérifier si le seuil de progression est atteint pour passer à la phase suivante
    threshold = PDCA_PROGRESS_THRESHOLDS.get(current_phase, 100)
    if progress >= threshold:
        current_idx = PDCA_SEQUENCE.index(current_phase)
        if current_idx < len(PDCA_SEQUENCE) - 1:
            return PDCA_SEQUENCE[current_idx + 1]

    return current_phase


def get_pdca_distribution(db: Session) -> dict[str, Any]:
    """
    Retourne le nombre de projets actifs par phase PDCA.
    Inclut uniquement les projets non supprimés et non annulés.
    """
    from app.models.project import Project

    results = db.execute(
        select(Project.lean_phase, func.count(Project.id).label("count"))
        .where(
            Project.is_deleted == False,  # noqa: E712
            Project.status != "cancelled",
        )
        .group_by(Project.lean_phase)
    ).all()

    # Initialiser toutes les phases à 0
    distribution: dict[str, int] = {phase: 0 for phase in PDCA_SEQUENCE}

    for row in results:
        if row.lean_phase in distribution:
            distribution[row.lean_phase] = row.count

    return distribution


def get_pdca_projects_by_phase(db: Session) -> dict[str, list]:
    """
    Retourne les projets groupés par phase PDCA pour le tableau Kanban PDCA.
    """
    from app.models.project import Project

    projects = db.execute(
        select(Project).where(
            Project.is_deleted == False,  # noqa: E712
            Project.status != "cancelled",
        )
    ).scalars().all()

    grouped: dict[str, list] = {phase: [] for phase in PDCA_SEQUENCE}

    for project in projects:
        if project.lean_phase in grouped:
            grouped[project.lean_phase].append(project)

    return grouped
