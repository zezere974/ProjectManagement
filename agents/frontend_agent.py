"""
Agent Frontend — Templates Jinja2, HTMX, Alpine.js et gestion visuelle Lean.

Responsabilités :
- Créer et maintenir les templates Jinja2 (base, pages, partiels HTMX)
- Implémenter les interactions HTMX (mises à jour partielles sans rechargement)
- Gérer l'état côté client avec Alpine.js
- Appliquer le thème industriel / Lean Visual Management sombre
- Implémenter le système de codes couleur Lean :
  * done/act : #22c55e (vert)
  * in_progress/do : #3b82f6 (bleu)
  * blocked/critical : #ef4444 (rouge)
  * check/medium : #eab308 (jaune)
  * high/escalation : #f97316 (orange)
  * backlog/plan/cancelled : #6b7280 (gris)
- Développer le timer standup 15 minutes (Alpine.js)
- Gérer la navigation responsive (sidebar mobile)
- Implémenter les modales (ajout membre, modification projet)

Pages Phase 1 :
- / → redirect
- /login — authentification avec bouton SSO désactivé
- /dashboard — KPIs, Kanban PDCA, alertes, humeur équipe
- /projects — liste avec filtres, toggle vue carte/liste, export
- /projects/{id} — détail : tâches inline, log quotidien, historique
- /stand-up — vue plein écran avec timer, standup par responsable
- /team — tableau membres, charge de travail, modales HTMX
- /reports — placeholder Phase 2

Templates partiels HTMX :
- partials/project_card.html — carte projet réutilisable
- partials/task_item.html — ligne tâche avec checkbox
- partials/alert_item.html — alerte avec bouton résolution
- partials/daily_log_form.html — formulaire standup sans rechargement
- partials/project_status_badge.html — badge statut

Phase 2 — Extensions :
- Page de rapports interactive avec aperçu
- Graphiques KPI avec Chart.js ou D3.js

Phase 3 — Extensions :
- Notifications en temps réel via WebSocket ou SSE
- Indicateurs Teams en ligne
"""

AGENT_NAME = "FrontendAgent"
AGENT_VERSION = "1.0.0"
AGENT_PHASE = 1
AGENT_STATUS = "active"
