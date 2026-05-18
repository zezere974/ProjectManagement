"""
Agent Teams — Intégration Microsoft Teams (Phase 3).

Statut : INACTIF en Phase 1 et Phase 2

Responsabilités (Phase 3) :
- Envoyer des notifications d'alertes via webhooks Teams
- Publier des résumés hebdomadaires automatiques dans des canaux Teams
- Notifier en temps réel des changements de statut de projets critiques
- Gérer les abonnements aux canaux et les webhooks
- Implémenter le retry/backoff pour la résilience des notifications

Dépendances Phase 3 (requirements-phase3.txt) :
- aiohttp>=3.9 — Requêtes HTTP asynchrones vers Teams
- apscheduler>=3.10 — Planification des envois hebdomadaires
- azure-storage-blob>=12.19 — Stockage des fichiers de rapport

Types de notifications :
- alert : Nouvelle alerte créée sur un projet (si TEAMS_NOTIFY_ON_ALERT=true)
- flag : Projet signalé (si TEAMS_NOTIFY_ON_FLAG=true)
- done : Projet terminé (si TEAMS_NOTIFY_ON_DONE=true)
- weekly_recap : Récapitulatif hebdomadaire (cron TEAMS_WEEKLY_RECAP_CRON)

Configuration requise (.env) :
- TEAMS_ENABLED=true
- TEAMS_DEFAULT_WEBHOOK_URL — URL du webhook Teams par défaut
- TEAMS_NOTIFY_ON_ALERT=true
- TEAMS_NOTIFY_ON_FLAG=true
- TEAMS_NOTIFY_ON_DONE=false
- TEAMS_WEEKLY_RECAP_CRON="0 8 * * MON"

Par équipe (modèle Team) :
- teams_channel_id — ID du canal Teams
- teams_webhook_url — URL du webhook spécifique à l'équipe
"""

AGENT_NAME = "TeamsAgent"
AGENT_VERSION = "0.0.1"
AGENT_PHASE = 3
AGENT_STATUS = "inactive"


async def send_alert_notification(*args, **kwargs):
    """Phase 3 — Non implémenté."""
    raise NotImplementedError("Teams integration disponible en Phase 3")


async def send_weekly_recap(*args, **kwargs):
    """Phase 3 — Non implémenté."""
    raise NotImplementedError("Teams integration disponible en Phase 3")
