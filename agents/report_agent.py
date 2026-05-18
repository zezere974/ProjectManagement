"""
Agent Rapports — Génération Excel, PDF, PowerPoint (Phase 2).

Statut : INACTIF en Phase 1

Responsabilités (Phase 2) :
- Générer des rapports hebdomadaires automatiques (Excel + PDF)
- Produire des tableaux de bord PowerPoint pour les revues de direction
- Exporter les KPIs par équipe en format tabulaire
- Générer des rapports de projet détaillés
- Planifier la génération automatique via APScheduler
- Stocker les rapports dans le système de fichiers ou Azure Blob Storage

Dépendances Phase 2 (requirements-phase2.txt) :
- openpyxl>=3.1 — Export Excel
- python-pptx>=1.0 — Export PowerPoint
- weasyprint>=62.0 — Export PDF
- msal>=1.28 — Authentification Azure pour SSO

Types de rapports :
- weekly : Bilan hebdomadaire projets + alertes + KPIs
- monthly : Rapport mensuel avec tendances et projections
- project : Rapport détaillé d'un projet
- team_kpi : Tableau de bord KPIs par équipe

Formats de sortie :
- Excel (.xlsx) — tableaux de données interactifs
- PDF (.pdf) — rapports formatés pour impression
- PowerPoint (.pptx) — présentations pour revues de direction

Phase 3 — Extensions :
- Envoi automatique des rapports via Teams
- Stockage dans Azure Blob Storage
- Génération à la demande via API
"""

AGENT_NAME = "ReportAgent"
AGENT_VERSION = "0.1.0"
AGENT_PHASE = 2
AGENT_STATUS = "inactive"


def generate_weekly_report(*args, **kwargs):
    """Phase 2 — Non implémenté."""
    raise NotImplementedError("Rapports disponibles en Phase 2")
