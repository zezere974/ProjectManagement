# Tests d'intégration API — routes principales
import pytest


class TestHealthCheck:
    """Tests du healthcheck."""

    def test_health_check(self, client):
        """Le healthcheck répond correctement."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "phase" in data


class TestDashboardAPI:
    """Tests de l'API tableau de bord."""

    def test_dashboard_api(self, client, admin_token):
        """L'API tableau de bord retourne les données correctement."""
        response = client.get(
            "/api/dashboard",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "kpis" in data
        assert "active_alerts" in data
        assert "flagged_projects" in data
        assert "pdca_distribution" in data

    def test_dashboard_api_unauthorized(self, client):
        """L'API tableau de bord est protégée."""
        response = client.get("/api/dashboard")
        assert response.status_code == 401


class TestAlertsAPI:
    """Tests de l'API alertes."""

    def test_list_alerts(self, client, admin_token):
        """Liste des alertes accessible."""
        response = client.get(
            "/api/alerts",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_create_alert(self, client, admin_token, sample_project):
        """Création d'une alerte."""
        response = client.post(
            "/api/alerts",
            json={
                "project_id": sample_project.id,
                "type": "blocker",
                "message": "Test alerte blocage",
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["type"] == "blocker"
        assert data["is_resolved"] is False

    def test_resolve_alert(self, client, admin_token, db, sample_project, admin_user):
        """Résolution d'une alerte."""
        from app.models.alert import Alert
        alert = Alert(
            project_id=sample_project.id,
            created_by_id=admin_user.id,
            type="delay",
            message="Test alerte",
            is_resolved=False,
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)

        response = client.put(
            f"/api/alerts/{alert.id}/resolve",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_resolved"] is True
        assert data["resolved_at"] is not None

    def test_filter_alerts_by_resolved(self, client, admin_token, db, sample_project, admin_user):
        """Filtre des alertes par statut de résolution."""
        from app.models.alert import Alert
        alert = Alert(
            project_id=sample_project.id,
            created_by_id=admin_user.id,
            type="resource",
            message="Test",
            is_resolved=False,
        )
        db.add(alert)
        db.commit()

        response = client.get(
            "/api/alerts?resolved=false",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert all(not a["is_resolved"] for a in data)


class TestTasksAPI:
    """Tests de l'API tâches."""

    def test_list_tasks_for_project(self, client, admin_token, sample_project):
        """Liste des tâches d'un projet."""
        response = client.get(
            f"/api/projects/{sample_project.id}/tasks",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_create_task(self, client, member_token, sample_project):
        """Création d'une tâche."""
        response = client.post(
            f"/api/projects/{sample_project.id}/tasks",
            json={
                "title": "Installer le pare-feu",
                "status": "todo",
                "is_quick_win": True,
            },
            headers={"Authorization": f"Bearer {member_token}"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Installer le pare-feu"
        assert data["is_quick_win"] is True

    def test_update_task_status_to_done(self, client, member_token, db, sample_project, member_user):
        """Mise à jour du statut d'une tâche vers done."""
        from app.models.task import Task
        task = Task(
            project_id=sample_project.id,
            assigned_to_id=member_user.id,
            title="Tâche test",
            status="todo",
        )
        db.add(task)
        db.commit()
        db.refresh(task)

        response = client.put(
            f"/api/tasks/{task.id}",
            json={"status": "done"},
            headers={"Authorization": f"Bearer {member_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "done"
        assert data["completed_at"] is not None

    def test_delete_task(self, client, admin_token, db, sample_project, admin_user):
        """Suppression d'une tâche."""
        from app.models.task import Task
        task = Task(
            project_id=sample_project.id,
            title="Tâche à supprimer",
            status="todo",
        )
        db.add(task)
        db.commit()
        db.refresh(task)

        response = client.delete(
            f"/api/tasks/{task.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 204


class TestPhase2And3Routes:
    """Tests des routes Phase 2 et 3 (doivent retourner 501)."""

    def test_reports_weekly_returns_501(self, client, admin_token):
        """Les rapports retournent 501 en Phase 1."""
        response = client.get(
            "/api/reports/weekly",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 501

    def test_teams_notification_returns_501(self, client, admin_token):
        """Les notifications Teams retournent 501 en Phase 1."""
        response = client.post(
            "/api/notifications/teams/test",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 501
