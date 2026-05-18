"""
Agent Tests — Tests automatisés pytest et contrôle qualité.

Responsabilités :
- Maintenir et exécuter la suite de tests pytest
- Assurer la couverture des fonctionnalités critiques
- Tester la compatibilité SQLite / MSSQL des modèles
- Valider les permissions et restrictions de rôle
- Tester la logique Lean (délais, KPIs, PDCA, alertes)
- Fournir des fixtures réutilisables (base de données en mémoire, utilisateurs)

Structure des tests :
- tests/conftest.py — Fixtures partagées (db, client, users, tokens)
- tests/test_auth.py — Authentification, JWT, rate limiting
- tests/test_projects.py — CRUD projets, filtres, signalement, export
- tests/test_team.py — Membres, équipes, permissions par rôle
- tests/test_lean_logic.py — Délais, couleurs, alertes auto, KPI, PDCA
- tests/test_api.py — Tests d'intégration des routes principales
- tests/test_db_compat.py — Compatibilité modèles SQLite + MSSQL

Commandes d'exécution :
    # Tous les tests
    pytest tests/ -v

    # Tests d'authentification uniquement
    pytest tests/test_auth.py -v

    # Tests avec couverture
    pytest tests/ --cov=app --cov-report=html

    # Tests rapides (sans les tests lents)
    pytest tests/ -v -m "not slow"

Règles de qualité :
- Chaque route API doit avoir au moins un test positif et un test négatif
- Les restrictions de rôle doivent être systématiquement testées
- Les modèles doivent être testés pour leur compatibilité cross-dialecte
- Les services Lean doivent avoir des tests unitaires indépendants
"""

AGENT_NAME = "TestAgent"
AGENT_VERSION = "1.0.0"
AGENT_PHASE = 1
AGENT_STATUS = "active"


def run_tests(coverage: bool = False, verbose: bool = True) -> int:
    """Lance la suite de tests pytest et retourne le code de sortie."""
    import subprocess
    import sys

    cmd = [sys.executable, "-m", "pytest", "tests/"]
    if verbose:
        cmd.append("-v")
    if coverage:
        cmd.extend(["--cov=app", "--cov-report=html", "--cov-report=term-missing"])

    result = subprocess.run(cmd)
    return result.returncode
