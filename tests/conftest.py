# Fixtures pytest — client de test, base de données en mémoire, utilisateurs de test
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.database import Base, get_db
from app.models.user import User
from app.routers.auth import hash_password

# Base de données SQLite fichier temporaire pour les tests
# Note: SQLite en mémoire (:memory:) ne partage pas l'état entre connexions,
# donc on utilise un fichier temporaire partagé via une connexion unique
import os
import tempfile

# Connexion partagée pour SQLite (évite les problèmes de tables non visibles)
TEST_DB_FILE = "/tmp/test_daily_mgmt.db"
TEST_DATABASE_URL = f"sqlite:///{TEST_DB_FILE}"

# Moteur de test avec connexion persistante
from sqlalchemy.pool import StaticPool
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function")
def db():
    """Fixture de base de données — crée les tables et les supprime après le test."""
    # Import des modèles pour que SQLAlchemy les enregistre
    from app.models import User, Team, Project, Task, DailyLog, Alert, ReportExport  # noqa: F401

    Base.metadata.create_all(bind=test_engine)
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db):
    """Fixture client de test FastAPI avec override de la dépendance get_db."""
    from app.main import app
    import app.database as db_module

    def override_get_db():
        test_session = TestSessionLocal()
        try:
            yield test_session
        finally:
            test_session.close()

    # Patcher init_db pour qu'elle ne tourne pas sur la vraie DB lors des tests
    original_init_db = db_module.init_db
    def mock_init_db():
        pass  # No-op pendant les tests
    db_module.init_db = mock_init_db

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app, raise_server_exceptions=True) as c:
        yield c

    # Restaurer init_db et les overrides
    db_module.init_db = original_init_db
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def admin_user(db):
    """Fixture utilisateur admin de test."""
    user = User(
        email="admin@test.local",
        username="admin_test",
        hashed_password=hash_password("Admin123!"),
        role="admin",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture(scope="function")
def manager_user(db):
    """Fixture utilisateur manager de test."""
    user = User(
        email="manager@test.local",
        username="manager_test",
        hashed_password=hash_password("Manager123!"),
        role="manager",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture(scope="function")
def member_user(db):
    """Fixture utilisateur membre de test."""
    user = User(
        email="member@test.local",
        username="member_test",
        hashed_password=hash_password("Member123!"),
        role="member",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture(scope="function")
def admin_token(client, admin_user):
    """Fixture token JWT pour l'admin."""
    response = client.post(
        "/auth/login",
        json={"email": "admin@test.local", "password": "Admin123!"},
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    return response.json()["access_token"]


@pytest.fixture(scope="function")
def manager_token(client, manager_user):
    """Fixture token JWT pour le manager."""
    response = client.post(
        "/auth/login",
        json={"email": "manager@test.local", "password": "Manager123!"},
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    return response.json()["access_token"]


@pytest.fixture(scope="function")
def member_token(client, member_user):
    """Fixture token JWT pour le membre."""
    response = client.post(
        "/auth/login",
        json={"email": "member@test.local", "password": "Member123!"},
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    return response.json()["access_token"]


@pytest.fixture(scope="function")
def sample_team(db, manager_user):
    """Fixture équipe de test."""
    from app.models.team import Team
    team = Team(
        name="Équipe Test OT",
        description="Équipe de test cybersécurité OT",
        manager_id=manager_user.id,
        color_code="#3b82f6",
    )
    db.add(team)
    db.commit()
    db.refresh(team)
    return team


@pytest.fixture(scope="function")
def sample_project(db, sample_team, manager_user):
    """Fixture projet de test."""
    from datetime import date, timedelta
    from app.models.project import Project
    project = Project(
        name="Projet Test Firewall OT",
        description="Projet de test pour les tests unitaires",
        team_id=sample_team.id,
        owner_id=manager_user.id,
        status="in_progress",
        priority="high",
        lean_phase="do",
        progress_pct=50,
        start_date=date.today() - timedelta(days=10),
        target_date=date.today() + timedelta(days=20),
        kpi_target=100.0,
        kpi_actual=50.0,
        kpi_unit="%",
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project
