# Service Lean — calculs de délais, suggestion de statut et codes couleur visuels
from datetime import date
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.project import Project


# Correspondance couleurs Lean / Visual Management
LEAN_COLORS: dict[str, str] = {
    # Statuts
    "done": "#22c55e",
    "in_progress": "#3b82f6",
    "blocked": "#ef4444",
    "backlog": "#6b7280",
    "cancelled": "#6b7280",
    # Priorités
    "critical": "#ef4444",
    "high": "#f97316",
    "medium": "#eab308",
    "low": "#22c55e",
    # Phases PDCA
    "plan": "#6b7280",
    "do": "#3b82f6",
    "check": "#eab308",
    "act": "#22c55e",
    # Alertes
    "delay": "#eab308",
    "blocker": "#ef4444",
    "quality": "#f97316",
    "resource": "#f97316",
    "escalation": "#ef4444",
    # États génériques
    "at_risk": "#eab308",
    "ok": "#22c55e",
}


def calculate_delay(project: "Project") -> int:
    """
    Calcule le retard en jours d'un projet.
    Valeur négative = projet en avance.
    Valeur positive = projet en retard.
    0 si pas de date cible définie.
    """
    if project.target_date is None:
        return 0

    today = date.today()

    # Si le projet est terminé, calculer le retard par rapport à la date de fin réelle
    if project.status == "done" and project.actual_end_date is not None:
        return (project.actual_end_date - project.target_date).days

    # Si le projet est toujours en cours, comparer avec aujourd'hui
    return (today - project.target_date).days


def suggest_status(project: "Project") -> str:
    """
    Suggère un statut basé sur les dates et la progression du projet.
    Retourne le statut suggéré.
    """
    if project.status in ("done", "cancelled"):
        return project.status

    delay = calculate_delay(project)
    progress = project.progress_pct

    # Déjà bloqué
    if project.status == "blocked":
        return "blocked"

    # En retard significatif
    if delay > 7:
        return "blocked"

    # Progression nulle mais date dépassée
    if delay > 0 and progress == 0:
        return "blocked"

    # En avance ou dans les temps
    if progress == 100:
        return "done"

    if progress > 0:
        return "in_progress"

    return "backlog"


def get_lean_color(status: str = "", lean_phase: str = "", priority: str = "") -> str:
    """
    Retourne le code couleur hexadécimal selon le statut, la phase Lean ou la priorité.
    Priorité de résolution : statut > phase > priorité.
    """
    if status and status in LEAN_COLORS:
        return LEAN_COLORS[status]

    if lean_phase and lean_phase in LEAN_COLORS:
        return LEAN_COLORS[lean_phase]

    if priority and priority in LEAN_COLORS:
        return LEAN_COLORS[priority]

    # Couleur par défaut : gris
    return "#6b7280"


def get_progress_color(progress_pct: int, target_pct: float = 80.0) -> str:
    """
    Retourne la couleur de progression selon le pourcentage d'avancement.
    """
    if progress_pct >= 100:
        return "#22c55e"  # Vert — terminé
    if progress_pct >= target_pct:
        return "#3b82f6"  # Bleu — sur la bonne voie
    if progress_pct >= target_pct * 0.6:
        return "#eab308"  # Jaune — attention
    return "#ef4444"  # Rouge — en retard
