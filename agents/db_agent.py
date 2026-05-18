"""
Agent Base de données — SQLAlchemy, migrations Alembic et compatibilité multi-dialecte.

Responsabilités :
- Définir et maintenir les modèles SQLAlchemy 2.x
- Assurer la compatibilité SQLite / MS SQL Server
- Gérer les migrations Alembic (render_as_batch=True pour SQLite)
- Implémenter le seeding des données de démonstration IIoT/OT
- Optimiser les requêtes (index, relations eager/lazy loading)
- Gérer les transactions et la cohérence des données

Règles de compatibilité cross-dialecte :
- Utiliser uniquement : String(n), Integer, Boolean, Float, Date, DateTime, Text
- Ne pas utiliser : JSON, ARRAY, JSONB, AUTOINCREMENT (SQLite-only)
- Toujours spécifier la longueur des colonnes String
- Utiliser render_as_batch=True dans Alembic pour SQLite
- Ne pas utiliser de fonctions SQL spécifiques à un dialecte

Modèles Phase 1 :
- User — authentification, rôles, SSO stub
- Team — équipes avec manager et couleur Lean
- Project — projets PDCA avec KPIs et métadonnées Lean
- Task — tâches liées aux projets
- DailyLog — journaux standup quotidiens
- Alert — alertes et escalades
- ReportExport — squelette Phase 2

Phase 2 — Extensions :
- Connexion MS SQL Server via pyodbc
- Index de performance sur les colonnes fréquemment filtrées

Phase 3 — Extensions :
- Archivage des données historiques
- Partitionnement des logs
"""

AGENT_NAME = "DatabaseAgent"
AGENT_VERSION = "1.0.0"
AGENT_PHASE = 1
AGENT_STATUS = "active"
