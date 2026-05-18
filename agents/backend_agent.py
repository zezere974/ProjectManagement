"""
Agent Backend — Gestion des routes FastAPI et de la logique métier.

Responsabilités :
- Implémenter et maintenir toutes les routes FastAPI (API et pages HTML)
- Gérer la logique métier : création, modification, suppression de ressources
- Implémenter les filtres, la pagination et la recherche
- Gérer les exports CSV/JSON
- Implémenter les middlewares (CORS, sécurité, rate limiting)
- Valider les données via les schémas Pydantic v2
- Gérer les codes d'erreur HTTP (401, 403, 404, 422, 501)

Phase 1 — Routes actives :
- /auth/* — Authentification JWT
- /api/dashboard — KPIs globaux
- /api/projects/* — CRUD projets, signalement, journaux, export
- /api/tasks/* — Gestion des tâches
- /api/team/* — Gestion des membres et équipes
- /api/alerts/* — Alertes et résolution
- /api/reports/* — Phase 2 (501)
- /api/notifications/* — Phase 3 (501)

Phase 2 — Extensions prévues :
- Génération de rapports Excel/PDF/PPTX
- Intégration SSO MSAL

Phase 3 — Extensions prévues :
- Webhooks Teams
- Scheduler APScheduler pour les rappels
"""

AGENT_NAME = "BackendAgent"
AGENT_VERSION = "1.0.0"
AGENT_PHASE = 1
AGENT_STATUS = "active"
