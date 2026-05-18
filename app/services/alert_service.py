# Service alertes — détection automatique et gestion des alertes projet
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.alert import Alert
from app.services.lean_service import calculate_delay

if TYPE_CHECKING:
    from app.models.project import Project


def check_and_create_alerts(db: Session, project: "Project") -> list[Alert]:
    """
    Vérifie les conditions d'alerte et crée automatiquement des alertes si nécessaire.
    Conditions :
    - Projet bloqué depuis plus de 2 jours
    - Retard dépassant 20% de la durée totale
    Retourne la liste des nouvelles alertes créées.
    """
    new_alerts: list[Alert] = []

    # Récupérer le créateur par défaut (premier admin ou owner du projet)
    creator_id = project.owner_id or 1

    # Vérification : projet bloqué
    if project.status == "blocked":
        # Vérifier s'il n'existe pas déjà une alerte blocker non résolue
        existing = db.execute(
            select(Alert).where(
                Alert.project_id == project.id,
                Alert.type == "blocker",
                Alert.is_resolved == False,  # noqa: E712
            )
        ).scalars().first()

        if not existing:
            alert = Alert(
                project_id=project.id,
                created_by_id=creator_id,
                type="blocker",
                message=(
                    f"Le projet '{project.name}' est bloqué. "
                    "Action requise pour débloquer la situation."
                ),
                is_resolved=False,
                teams_notified=False,
            )
            db.add(alert)
            new_alerts.append(alert)

    # Vérification : retard dépassant 20% de la durée totale
    if project.target_date is not None and project.start_date is not None:
        from datetime import date
        total_duration = (project.target_date - project.start_date).days
        delay_days = calculate_delay(project)

        if total_duration > 0 and delay_days > 0:
            delay_pct = (delay_days / total_duration) * 100

            if delay_pct >= 20:
                # Vérifier s'il n'existe pas déjà une alerte de retard non résolue
                existing_delay = db.execute(
                    select(Alert).where(
                        Alert.project_id == project.id,
                        Alert.type == "delay",
                        Alert.is_resolved == False,  # noqa: E712
                    )
                ).scalars().first()

                if not existing_delay:
                    alert = Alert(
                        project_id=project.id,
                        created_by_id=creator_id,
                        type="delay",
                        message=(
                            f"Le projet '{project.name}' accuse un retard de {delay_days} jours "
                            f"({delay_pct:.0f}% de la durée totale). Revue nécessaire."
                        ),
                        is_resolved=False,
                        teams_notified=False,
                    )
                    db.add(alert)
                    new_alerts.append(alert)

    if new_alerts:
        db.commit()
        for alert in new_alerts:
            db.refresh(alert)

    return new_alerts


def resolve_alert(db: Session, alert_id: int, user_id: int) -> Alert:
    """
    Marque une alerte comme résolue par l'utilisateur spécifié.
    Retourne l'alerte mise à jour.
    """
    alert = db.execute(
        select(Alert).where(Alert.id == alert_id)
    ).scalars().first()

    if alert is None:
        raise ValueError(f"Alerte {alert_id} introuvable")

    alert.is_resolved = True
    alert.resolved_at = datetime.utcnow()
    alert.resolved_by_id = user_id

    db.commit()
    db.refresh(alert)
    return alert
