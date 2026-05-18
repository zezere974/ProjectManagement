# Tests d'authentification — connexion, tokens JWT, rate limiting
import pytest
from fastapi.testclient import TestClient


class TestLogin:
    """Tests de la route de connexion."""

    def test_login_valid_credentials(self, client, admin_user):
        """Connexion réussie avec credentials valides."""
        response = client.post(
            "/auth/login",
            json={"email": "admin@test.local", "password": "Admin123!"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_login_invalid_password(self, client, admin_user):
        """Connexion refusée avec mauvais mot de passe."""
        response = client.post(
            "/auth/login",
            json={"email": "admin@test.local", "password": "WrongPassword!"},
        )
        assert response.status_code == 401

    def test_login_invalid_email(self, client):
        """Connexion refusée avec email inexistant."""
        response = client.post(
            "/auth/login",
            json={"email": "nobody@test.local", "password": "Admin123!"},
        )
        assert response.status_code == 401

    def test_login_missing_fields(self, client):
        """Connexion refusée sans credentials."""
        response = client.post(
            "/auth/login",
            json={"email": "", "password": ""},
        )
        assert response.status_code in (401, 422)

    def test_login_inactive_user(self, client, db, admin_user):
        """Connexion refusée pour un utilisateur inactif."""
        admin_user.is_active = False
        db.commit()

        response = client.post(
            "/auth/login",
            json={"email": "admin@test.local", "password": "Admin123!"},
        )
        assert response.status_code in (401, 403)

    def test_login_sets_cookie(self, client, admin_user):
        """La connexion positionne bien le cookie JWT."""
        response = client.post(
            "/auth/login",
            json={"email": "admin@test.local", "password": "Admin123!"},
        )
        assert response.status_code == 200
        assert "access_token" in response.cookies


class TestRefreshToken:
    """Tests du rafraîchissement de token."""

    def test_refresh_valid_token(self, client, admin_user, admin_token):
        """Rafraîchissement réussi avec un refresh token valide."""
        # D'abord, récupérer le refresh token
        login_resp = client.post(
            "/auth/login",
            json={"email": "admin@test.local", "password": "Admin123!"},
        )
        refresh_token = login_resp.json()["refresh_token"]

        response = client.post(
            "/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert response.status_code == 200
        assert "access_token" in response.json()

    def test_refresh_invalid_token(self, client):
        """Rafraîchissement refusé avec un token invalide."""
        response = client.post(
            "/auth/refresh",
            json={"refresh_token": "invalid.token.here"},
        )
        assert response.status_code == 401


class TestLogout:
    """Tests de la déconnexion."""

    def test_logout_success(self, client, admin_token):
        """Déconnexion réussie."""
        response = client.post(
            "/auth/logout",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200


class TestGetCurrentUser:
    """Tests de récupération de l'utilisateur courant."""

    def test_get_me_authenticated(self, client, admin_user, admin_token):
        """Récupération réussie de l'utilisateur courant."""
        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "admin@test.local"
        assert data["role"] == "admin"
        assert "hashed_password" not in data

    def test_get_me_unauthenticated(self, client):
        """Retour 401 si non authentifié."""
        response = client.get("/auth/me")
        assert response.status_code == 401

    def test_get_me_invalid_token(self, client):
        """Retour 401 avec token invalide."""
        response = client.get(
            "/auth/me",
            headers={"Authorization": "Bearer invalid.token"},
        )
        assert response.status_code == 401


class TestRoleRequirement:
    """Tests des restrictions de rôle."""

    def test_admin_can_access_admin_route(self, client, admin_token):
        """Un admin peut accéder aux routes admin."""
        response = client.get(
            "/api/team",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200

    def test_member_cannot_create_project(self, client, member_token, sample_team):
        """Un membre ne peut pas créer un projet (rôle insuffisant)."""
        response = client.post(
            "/api/projects",
            json={
                "name": "Test Projet",
                "status": "backlog",
                "priority": "medium",
                "lean_phase": "plan",
            },
            headers={"Authorization": f"Bearer {member_token}"},
        )
        assert response.status_code == 403
