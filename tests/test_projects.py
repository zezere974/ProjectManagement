# Tests des projets — CRUD, filtres, signalement, journaux, suppression logique
import pytest
from datetime import date, timedelta


class TestProjectCRUD:
    """Tests CRUD des projets."""

    def test_list_projects_authenticated(self, client, admin_token, sample_project):
        """Liste des projets accessible à un utilisateur authentifié."""
        response = client.get(
            "/api/projects",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_list_projects_unauthenticated(self, client):
        """Liste des projets inaccessible sans authentification."""
        response = client.get("/api/projects")
        assert response.status_code == 401

    def test_create_project_as_manager(self, client, manager_token, sample_team):
        """Création de projet réussie en tant que manager."""
        response = client.post(
            "/api/projects",
            json={
                "name": "Nouveau Projet Firewall",
                "description": "Description test",
                "team_id": sample_team.id,
                "status": "backlog",
                "priority": "high",
                "lean_phase": "plan",
                "progress_pct": 0,
            },
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Nouveau Projet Firewall"
        assert data["status"] == "backlog"
        assert data["is_deleted"] is False

    def test_create_project_as_member_fails(self, client, member_token):
        """Création de projet refusée pour un membre."""
        response = client.post(
            "/api/projects",
            json={"name": "Test", "status": "backlog", "priority": "low", "lean_phase": "plan"},
            headers={"Authorization": f"Bearer {member_token}"},
        )
        assert response.status_code == 403

    def test_get_project_detail(self, client, admin_token, sample_project):
        """Récupération du détail d'un projet."""
        response = client.get(
            f"/api/projects/{sample_project.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_project.id
        assert data["name"] == sample_project.name
        assert "tasks" in data
        assert "daily_logs" in data

    def test_get_project_not_found(self, client, admin_token):
        """Retour 404 pour un projet inexistant."""
        response = client.get(
            "/api/projects/99999",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 404

    def test_update_project(self, client, manager_token, sample_project):
        """Mise à jour d'un projet."""
        response = client.put(
            f"/api/projects/{sample_project.id}",
            json={"status": "blocked", "progress_pct": 60},
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "blocked"
        assert data["progress_pct"] == 60

    def test_soft_delete_project(self, client, manager_token, sample_project):
        """Suppression logique d'un projet."""
        response = client.delete(
            f"/api/projects/{sample_project.id}",
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        assert response.status_code == 204

        # Le projet ne doit plus apparaître dans la liste
        list_response = client.get(
            "/api/projects",
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        project_ids = [p["id"] for p in list_response.json()]
        assert sample_project.id not in project_ids


class TestProjectFilters:
    """Tests des filtres sur la liste des projets."""

    def test_filter_by_status(self, client, admin_token, sample_project):
        """Filtre par statut."""
        response = client.get(
            "/api/projects?status=in_progress",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert all(p["status"] == "in_progress" for p in data)

    def test_filter_by_priority(self, client, admin_token, sample_project):
        """Filtre par priorité."""
        response = client.get(
            "/api/projects?priority=high",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert all(p["priority"] == "high" for p in data)

    def test_filter_by_lean_phase(self, client, admin_token, sample_project):
        """Filtre par phase PDCA."""
        response = client.get(
            "/api/projects?lean_phase=do",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert all(p["lean_phase"] == "do" for p in data)

    def test_search_by_name(self, client, admin_token, sample_project):
        """Recherche textuelle dans le nom du projet."""
        response = client.get(
            "/api/projects?search=Firewall",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert any("Firewall" in p["name"] for p in data)


class TestProjectFlag:
    """Tests de signalement des projets."""

    def test_flag_project(self, client, member_token, sample_project):
        """Signalement d'un projet."""
        response = client.post(
            f"/api/projects/{sample_project.id}/flag",
            headers={"Authorization": f"Bearer {member_token}"},
        )
        assert response.status_code == 200
        assert response.json()["is_flagged"] is True

    def test_unflag_project(self, client, member_token, sample_project, db):
        """Retrait du signalement d'un projet."""
        sample_project.is_flagged = True
        db.commit()

        response = client.post(
            f"/api/projects/{sample_project.id}/unflag",
            headers={"Authorization": f"Bearer {member_token}"},
        )
        assert response.status_code == 200
        assert response.json()["is_flagged"] is False


class TestDailyLog:
    """Tests des journaux quotidiens."""

    def test_add_daily_log(self, client, member_token, sample_project):
        """Ajout d'un journal quotidien."""
        response = client.post(
            f"/api/projects/{sample_project.id}/daily-log",
            json={
                "log_date": date.today().isoformat(),
                "what_done": "Configuration des règles de filtrage",
                "what_planned": "Tests de connectivité",
                "blockers": None,
                "mood_score": 4,
            },
            headers={"Authorization": f"Bearer {member_token}"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["what_done"] == "Configuration des règles de filtrage"
        assert data["mood_score"] == 4

    def test_daily_log_invalid_mood(self, client, member_token, sample_project):
        """Erreur si le score d'humeur est hors plage."""
        response = client.post(
            f"/api/projects/{sample_project.id}/daily-log",
            json={
                "log_date": date.today().isoformat(),
                "what_done": "Test",
                "what_planned": "Test",
                "mood_score": 10,  # Invalide (max 5)
            },
            headers={"Authorization": f"Bearer {member_token}"},
        )
        assert response.status_code == 422


class TestProjectExport:
    """Tests de l'export des projets."""

    def test_export_csv(self, client, admin_token, sample_project):
        """Export CSV des projets."""
        response = client.get(
            "/api/export/projects?format=csv",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]

    def test_export_json(self, client, admin_token, sample_project):
        """Export JSON des projets."""
        response = client.get(
            "/api/export/projects?format=json",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
