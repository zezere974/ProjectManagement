#!/usr/bin/env python3
"""
Orchestrateur de l'application Daily Management.
Lit APP_PHASE depuis les variables d'environnement et décrit l'activation des agents.
"""
import sys
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s — %(levelname)s — %(message)s")
logger = logging.getLogger(__name__)


def check_app_phase() -> int:
    """Lit la phase applicative depuis la configuration."""
    try:
        from app.config import settings
        return settings.APP_PHASE
    except Exception as e:
        logger.error(f"Impossible de lire la configuration : {e}")
        return 1


def get_active_features(phase: int) -> dict:
    """Retourne les fonctionnalités actives selon la phase."""
    features = {
        "authentication": True,
        "projects_crud": True,
        "tasks_management": True,
        "daily_logs": True,
        "alerts": True,
        "dashboard_kpis": True,
        "pdca_kanban": True,
        "standup_timer": True,
        "team_management": True,
        "csv_export": True,
        # Phase 2
        "excel_reports": phase >= 2,
        "pdf_reports": phase >= 2,
        "pptx_reports": phase >= 2,
        "sso_msal": phase >= 2,
        "scheduled_reports": phase >= 2,
        # Phase 3
        "teams_notifications": phase >= 3,
        "teams_webhook": phase >= 3,
        "azure_blob_storage": phase >= 3,
        "background_scheduler": phase >= 3,
    }
    return features


def get_active_agents(phase: int) -> list[dict]:
    """Retourne les agents actifs selon la phase."""
    agents = [
        {
            "name": "BackendAgent",
            "module": "agents.backend_agent",
            "active": True,
            "description": "Gestion des routes FastAPI et de la logique métier",
        },
        {
            "name": "DatabaseAgent",
            "module": "agents.db_agent",
            "active": True,
            "description": "Gestion SQLAlchemy, migrations Alembic et compatibilité multi-dialecte",
        },
        {
            "name": "AuthAgent",
            "module": "agents.auth_agent",
            "active": True,
            "description": "Authentification JWT, bcrypt, gestion des rôles",
        },
        {
            "name": "FrontendAgent",
            "module": "agents.frontend_agent",
            "active": True,
            "description": "Templates Jinja2, HTMX, Alpine.js et gestion visuelle Lean",
        },
        {
            "name": "ReportAgent",
            "module": "agents.report_agent",
            "active": phase >= 2,
            "description": "Génération Excel/PDF/PPTX et exports automatisés (Phase 2)",
        },
        {
            "name": "TeamsAgent",
            "module": "agents.teams_agent",
            "active": phase >= 3,
            "description": "Intégration Microsoft Teams — webhooks et notifications (Phase 3)",
        },
        {
            "name": "TestAgent",
            "module": "agents.test_agent",
            "active": True,
            "description": "Tests automatisés pytest et contrôle qualité",
        },
    ]
    return agents


def print_startup_banner(phase: int) -> None:
    """Affiche la bannière de démarrage avec les informations de phase."""
    try:
        from app.config import settings
        db_type = "SQLite (local)" if settings.IS_SQLITE else "MS SQL Server"
        sso_status = "✓ Activé" if settings.SSO_ENABLED else "✗ Désactivé (Phase 2)"
        teams_status = "✓ Activé" if settings.TEAMS_ENABLED else "✗ Désactivé (Phase 3)"
    except Exception:
        db_type = "Inconnu"
        sso_status = "Non configuré"
        teams_status = "Non configuré"

    banner = f"""
╔══════════════════════════════════════════════════════════════════╗
║         DAILY MANAGEMENT APP — Phase {phase} — Démarrage             ║
╠══════════════════════════════════════════════════════════════════╣
║  Démarré le : {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}                       ║
║  Phase      : {phase}                                                  ║
║  Base de données : {db_type:<43} ║
║  SSO (MSAL) : {sso_status:<49} ║
║  Teams      : {teams_status:<49} ║
╠══════════════════════════════════════════════════════════════════╣
║  URL        : http://localhost:8000                              ║
║  Docs API   : http://localhost:8000/docs                         ║
╚══════════════════════════════════════════════════════════════════╝
"""
    print(banner)


def print_agents_status(phase: int) -> None:
    """Affiche le statut des agents."""
    agents = get_active_agents(phase)
    print("Agents disponibles :")
    for agent in agents:
        status = "✓ ACTIF " if agent["active"] else "○ INACTIF"
        print(f"  [{status}] {agent['name']:<20} — {agent['description']}")
    print()


def print_features_status(phase: int) -> None:
    """Affiche les fonctionnalités actives."""
    features = get_active_features(phase)
    print("Fonctionnalités actives :")
    for feature, active in features.items():
        status = "✓" if active else "✗"
        color_on = "" if active else ""
        print(f"  [{status}] {feature}")
    print()


def main():
    """Point d'entrée principal de l'orchestrateur."""
    phase = check_app_phase()

    print_startup_banner(phase)
    print_agents_status(phase)
    print_features_status(phase)

    if "--check" in sys.argv:
        # Mode vérification — juste afficher et quitter
        print("✓ Vérification de phase terminée.")
        return

    if "--start" in sys.argv:
        # Mode démarrage — lancer l'application
        import uvicorn
        print("Lancement de l'application...")
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
        )


if __name__ == "__main__":
    main()
