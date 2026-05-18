# Tests de la logique Lean — délais, alertes automatiques, KPI, PDCA
import pytest
from datetime import date, timedelta
from unittest.mock import MagicMock


class TestDelayCalculation:
    """Tests du calcul de délai."""

    def test_project_no_target_date(self):
        """Délai = 0 si pas de date cible."""
        from app.services.lean_service import calculate_delay
        project = MagicMock()
        project.target_date = None
        project.status = "in_progress"
        project.actual_end_date = None
        assert calculate_delay(project) == 0

    def test_project_on_time(self):
        """Délai négatif si date cible dans le futur."""
        from app.services.lean_service import calculate_delay
        project = MagicMock()
        project.target_date = date.today() + timedelta(days=10)
        project.status = "in_progress"
        project.actual_end_date = None
        delay = calculate_delay(project)
        assert delay < 0  # En avance

    def test_project_delayed(self):
        """Délai positif si date cible dépassée."""
        from app.services.lean_service import calculate_delay
        project = MagicMock()
        project.target_date = date.today() - timedelta(days=5)
        project.status = "in_progress"
        project.actual_end_date = None
        delay = calculate_delay(project)
        assert delay > 0
        assert delay == 5

    def test_project_done_on_time(self):
        """Délai = 0 pour un projet terminé dans les temps."""
        from app.services.lean_service import calculate_delay
        project = MagicMock()
        project.target_date = date.today()
        project.status = "done"
        project.actual_end_date = date.today()
        delay = calculate_delay(project)
        assert delay == 0

    def test_project_done_late(self):
        """Délai positif pour un projet terminé en retard."""
        from app.services.lean_service import calculate_delay
        project = MagicMock()
        project.target_date = date.today() - timedelta(days=3)
        project.status = "done"
        project.actual_end_date = date.today()
        delay = calculate_delay(project)
        assert delay == 3


class TestLeanColors:
    """Tests des codes couleur Lean."""

    def test_color_done(self):
        """Couleur verte pour les projets terminés."""
        from app.services.lean_service import get_lean_color
        assert get_lean_color(status="done") == "#22c55e"

    def test_color_blocked(self):
        """Couleur rouge pour les projets bloqués."""
        from app.services.lean_service import get_lean_color
        assert get_lean_color(status="blocked") == "#ef4444"

    def test_color_in_progress(self):
        """Couleur bleue pour les projets en cours."""
        from app.services.lean_service import get_lean_color
        assert get_lean_color(status="in_progress") == "#3b82f6"

    def test_color_backlog(self):
        """Couleur grise pour le backlog."""
        from app.services.lean_service import get_lean_color
        assert get_lean_color(status="backlog") == "#6b7280"

    def test_color_critical_priority(self):
        """Couleur rouge pour priorité critique."""
        from app.services.lean_service import get_lean_color
        assert get_lean_color(priority="critical") == "#ef4444"

    def test_color_pdca_plan(self):
        """Couleur grise pour la phase Plan."""
        from app.services.lean_service import get_lean_color
        assert get_lean_color(lean_phase="plan") == "#6b7280"

    def test_color_pdca_act(self):
        """Couleur verte pour la phase Act."""
        from app.services.lean_service import get_lean_color
        assert get_lean_color(lean_phase="act") == "#22c55e"

    def test_color_default(self):
        """Couleur grise par défaut."""
        from app.services.lean_service import get_lean_color
        assert get_lean_color() == "#6b7280"


class TestSuggestStatus:
    """Tests de suggestion de statut."""

    def test_suggest_done_for_completed(self):
        """Suggestion 'done' pour un projet à 100%."""
        from app.services.lean_service import suggest_status
        project = MagicMock()
        project.status = "in_progress"
        project.progress_pct = 100
        project.target_date = date.today() + timedelta(days=5)
        assert suggest_status(project) == "done"

    def test_suggest_blocked_for_overdue(self):
        """Suggestion 'blocked' pour un projet très en retard."""
        from app.services.lean_service import suggest_status
        project = MagicMock()
        project.status = "in_progress"
        project.progress_pct = 20
        project.target_date = date.today() - timedelta(days=10)
        assert suggest_status(project) == "blocked"


class TestAutoAlerts:
    """Tests des alertes automatiques."""

    def test_auto_alert_blocked_project(self, db, sample_project, manager_user):
        """Alerte automatique créée pour un projet bloqué."""
        from app.services.alert_service import check_and_create_alerts
        sample_project.status = "blocked"
        db.commit()

        alerts = check_and_create_alerts(db, sample_project)
        assert len(alerts) >= 1
        assert any(a.type == "blocker" for a in alerts)

    def test_no_duplicate_blocker_alert(self, db, sample_project, manager_user):
        """Pas d'alerte dupliquée si une alerte blocker existe déjà."""
        from app.services.alert_service import check_and_create_alerts
        from app.models.alert import Alert

        sample_project.status = "blocked"
        db.commit()

        # Première alerte
        alerts1 = check_and_create_alerts(db, sample_project)

        # Deuxième appel — ne doit pas créer de nouvelle alerte
        alerts2 = check_and_create_alerts(db, sample_project)
        assert len(alerts2) == 0

    def test_auto_alert_delayed_project(self, db, sample_project, manager_user):
        """Alerte automatique créée pour un projet en retard de plus de 20%."""
        from app.services.alert_service import check_and_create_alerts

        # Projet avec retard important
        sample_project.start_date = date.today() - timedelta(days=50)
        sample_project.target_date = date.today() - timedelta(days=10)
        sample_project.status = "in_progress"
        db.commit()

        alerts = check_and_create_alerts(db, sample_project)
        assert any(a.type == "delay" for a in alerts)


class TestPDCAService:
    """Tests du service PDCA."""

    def test_suggest_next_phase_plan_to_do(self):
        """Progression de Plan vers Do à partir de 25%."""
        from app.services.pdca_service import suggest_next_phase
        project = MagicMock()
        project.lean_phase = "plan"
        project.progress_pct = 30
        project.status = "in_progress"
        assert suggest_next_phase(project) == "do"

    def test_suggest_stay_plan_low_progress(self):
        """Rester en Plan si progression insuffisante."""
        from app.services.pdca_service import suggest_next_phase
        project = MagicMock()
        project.lean_phase = "plan"
        project.progress_pct = 10
        project.status = "in_progress"
        assert suggest_next_phase(project) == "plan"

    def test_suggest_act_for_done(self):
        """Retourner Act pour un projet terminé."""
        from app.services.pdca_service import suggest_next_phase
        project = MagicMock()
        project.lean_phase = "check"
        project.progress_pct = 100
        project.status = "done"
        assert suggest_next_phase(project) == "act"

    def test_pdca_distribution(self, db, sample_project):
        """Distribution PDCA correcte."""
        from app.services.pdca_service import get_pdca_distribution
        distribution = get_pdca_distribution(db)
        assert "plan" in distribution
        assert "do" in distribution
        assert "check" in distribution
        assert "act" in distribution


class TestKPIService:
    """Tests du service KPI."""

    def test_global_kpis_structure(self, db, sample_project):
        """Structure correcte des KPIs globaux."""
        from app.services.kpi_service import get_global_kpis
        kpis = get_global_kpis(db)
        assert "total_projects" in kpis
        assert "active_projects" in kpis
        assert "blocked_projects" in kpis
        assert "on_time_rate" in kpis
        assert "avg_mood" in kpis
        assert kpis["total_projects"] >= 1

    def test_team_kpis_empty(self, db):
        """KPIs équipe retourne des valeurs par défaut si aucun projet."""
        from app.services.kpi_service import get_team_kpis
        kpis = get_team_kpis(db, team_id=99999)
        assert kpis["total_projects"] == 0
        assert kpis["on_time_rate"] == 0.0
