# Tests équipe — membres, rôles, permissions
import pytest


class TestTeamMembers:
    """Tests de gestion des membres."""

    def test_list_members_authenticated(self, client, admin_token, admin_user):
        """Liste des membres accessible à un utilisateur authentifié."""
        response = client.get(
            "/api/team",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_add_member_as_admin(self, client, admin_token):
        """Ajout d'un membre réussi en tant qu'admin."""
        response = client.post(
            "/api/team/members",
            json={
                "email": "newuser@test.local",
                "username": "new_user",
                "password": "NewUser123!",
                "role": "member",
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@test.local"
        assert data["role"] == "member"
        assert "hashed_password" not in data

    def test_add_member_duplicate_email(self, client, admin_token, admin_user):
        """Ajout refusé si l'email est déjà utilisé."""
        response = client.post(
            "/api/team/members",
            json={
                "email": "admin@test.local",  # Email déjà pris
                "username": "autre_user",
                "password": "Test123!",
                "role": "member",
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 409

    def test_add_member_as_member_fails(self, client, member_token):
        """Ajout de membre refusé pour un simple membre."""
        response = client.post(
            "/api/team/members",
            json={
                "email": "other@test.local",
                "username": "other_user",
                "password": "Test123!",
                "role": "member",
            },
            headers={"Authorization": f"Bearer {member_token}"},
        )
        assert response.status_code == 403

    def test_update_member(self, client, admin_token, member_user):
        """Mise à jour d'un membre."""
        response = client.put(
            f"/api/team/members/{member_user.id}",
            json={"username": "updated_member"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        assert response.json()["username"] == "updated_member"

    def test_deactivate_member_as_admin(self, client, admin_token, member_user):
        """Désactivation d'un membre réussie en tant qu'admin."""
        response = client.delete(
            f"/api/team/members/{member_user.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 204

    def test_cannot_deactivate_self(self, client, admin_token, admin_user):
        """Un admin ne peut pas se désactiver lui-même."""
        response = client.delete(
            f"/api/team/members/{admin_user.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 400

    def test_deactivate_member_as_manager_fails(self, client, manager_token, member_user):
        """Désactivation refusée pour un manager."""
        response = client.delete(
            f"/api/team/members/{member_user.id}",
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        assert response.status_code == 403


class TestTeamPermissions:
    """Tests des permissions par rôle."""

    def test_admin_can_list_teams(self, client, admin_token, sample_team):
        """Un admin peut voir les équipes."""
        response = client.get(
            "/api/team/teams",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200

    def test_manager_cannot_create_team(self, client, manager_token):
        """Un manager ne peut pas créer une équipe (réservé aux admins)."""
        response = client.post(
            "/api/team/teams",
            json={
                "name": "Nouvelle Équipe",
                "color_code": "#3b82f6",
            },
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        assert response.status_code == 403

    def test_manager_cannot_create_admin(self, client, manager_token):
        """Un manager ne peut pas créer un autre manager ou admin."""
        response = client.post(
            "/api/team/members",
            json={
                "email": "newmanager@test.local",
                "username": "new_manager",
                "password": "Manager123!",
                "role": "manager",  # Le manager tente de créer un autre manager
            },
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        assert response.status_code == 403
