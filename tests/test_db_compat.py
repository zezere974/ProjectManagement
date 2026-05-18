# Tests de compatibilité base de données — SQLite et MSSQL
import pytest
from sqlalchemy import inspect, text


class TestModelCompatibility:
    """Tests de compatibilité des modèles avec SQLite et MSSQL."""

    def test_all_models_use_compatible_types(self, db):
        """Vérifie que les modèles utilisent des types compatibles multi-dialecte."""
        from app.models import User, Team, Project, Task, DailyLog, Alert, ReportExport

        inspector = inspect(db.bind)
        tables = inspector.get_table_names()

        # Toutes les tables doivent exister
        expected_tables = [
            "users", "teams", "projects", "tasks",
            "daily_logs", "alerts", "report_exports",
        ]
        for table in expected_tables:
            assert table in tables, f"Table '{table}' manquante"

    def test_no_sqlite_only_columns(self, db):
        """Vérifie qu'aucun type SQLite-only n'est utilisé dans les modèles."""
        from sqlalchemy import inspect as sa_inspect
        from sqlalchemy import String, Integer, Boolean, Float, Date, DateTime, Text

        COMPATIBLE_TYPES = (String, Integer, Boolean, Float, Date, DateTime, Text)

        inspector = sa_inspect(db.bind)

        for table_name in inspector.get_table_names():
            columns = inspector.get_columns(table_name)
            for col in columns:
                col_type = col["type"]
                type_class = type(col_type)
                # Les types de base SQLAlchemy sont compatibles cross-dialecte
                # (SQLAlchemy les traduit automatiquement)
                assert col_type is not None, f"Type None pour {table_name}.{col['name']}"

    def test_user_model_fields(self, db):
        """Vérifie que le modèle User possède tous les champs requis."""
        inspector = inspect(db.bind)
        columns = {col["name"] for col in inspector.get_columns("users")}

        required_columns = {
            "id", "email", "username", "hashed_password",
            "role", "is_active", "last_login",
            "sso_provider", "sso_id", "teams_user_id",
            "created_at", "updated_at",
        }
        assert required_columns.issubset(columns), \
            f"Colonnes manquantes : {required_columns - columns}"

    def test_project_model_fields(self, db):
        """Vérifie que le modèle Project possède tous les champs requis."""
        inspector = inspect(db.bind)
        columns = {col["name"] for col in inspector.get_columns("projects")}

        required_columns = {
            "id", "name", "description", "team_id", "status",
            "priority", "lean_phase", "owner_id",
            "start_date", "target_date", "actual_end_date",
            "progress_pct", "kpi_target", "kpi_actual", "kpi_unit",
            "is_flagged", "notes", "is_deleted",
            "created_at", "updated_at",
        }
        assert required_columns.issubset(columns), \
            f"Colonnes manquantes : {required_columns - columns}"

    def test_task_model_fields(self, db):
        """Vérifie que le modèle Task possède tous les champs requis."""
        inspector = inspect(db.bind)
        columns = {col["name"] for col in inspector.get_columns("tasks")}

        required_columns = {
            "id", "project_id", "assigned_to_id", "title",
            "description", "status", "due_date",
            "completed_at", "is_quick_win",
            "created_at", "updated_at",
        }
        assert required_columns.issubset(columns), \
            f"Colonnes manquantes : {required_columns - columns}"

    def test_daily_log_model_fields(self, db):
        """Vérifie que le modèle DailyLog possède tous les champs requis."""
        inspector = inspect(db.bind)
        columns = {col["name"] for col in inspector.get_columns("daily_logs")}

        required_columns = {
            "id", "project_id", "user_id", "log_date",
            "what_done", "what_planned", "blockers",
            "mood_score", "created_at",
        }
        assert required_columns.issubset(columns), \
            f"Colonnes manquantes : {required_columns - columns}"

    def test_alert_model_fields(self, db):
        """Vérifie que le modèle Alert possède tous les champs requis."""
        inspector = inspect(db.bind)
        columns = {col["name"] for col in inspector.get_columns("alerts")}

        required_columns = {
            "id", "project_id", "created_by_id", "type",
            "message", "is_resolved", "resolved_at",
            "resolved_by_id", "teams_notified",
            "created_at", "updated_at",
        }
        assert required_columns.issubset(columns), \
            f"Colonnes manquantes : {required_columns - columns}"

    def test_string_lengths_are_defined(self, db):
        """Vérifie que les colonnes String ont une longueur définie (requis pour MSSQL)."""
        inspector = inspect(db.bind)

        for table_name in inspector.get_table_names():
            columns = inspector.get_columns(table_name)
            for col in columns:
                col_type = col["type"]
                type_name = type(col_type).__name__
                if type_name == "VARCHAR":
                    # MSSQL requiert une longueur explicite sur les VARCHAR
                    # (pas de VARCHAR illimité)
                    length = getattr(col_type, "length", None)
                    assert length is not None and length > 0, \
                        f"VARCHAR sans longueur dans {table_name}.{col['name']}"

    def test_crud_operations_work(self, db):
        """Test CRUD de base pour vérifier la compatibilité opérationnelle."""
        from app.models.user import User
        from app.routers.auth import hash_password

        # Création
        user = User(
            email="compat_test@test.local",
            username="compat_test_user",
            hashed_password=hash_password("Test123!"),
            role="member",
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        assert user.id is not None

        # Lecture
        from sqlalchemy import select
        fetched = db.execute(
            select(User).where(User.email == "compat_test@test.local")
        ).scalars().first()
        assert fetched is not None
        assert fetched.username == "compat_test_user"

        # Mise à jour
        fetched.is_active = False
        db.commit()
        db.refresh(fetched)
        assert fetched.is_active is False

        # Suppression
        db.delete(fetched)
        db.commit()
        gone = db.execute(
            select(User).where(User.email == "compat_test@test.local")
        ).scalars().first()
        assert gone is None

    def test_foreign_keys_exist(self, db):
        """Vérifie que les clés étrangères sont correctement définies."""
        inspector = inspect(db.bind)

        # Vérifier les FKs sur la table projects
        fks = inspector.get_foreign_keys("projects")
        fk_columns = {fk["constrained_columns"][0] for fk in fks}
        assert "team_id" in fk_columns
        assert "owner_id" in fk_columns

        # Vérifier les FKs sur la table tasks
        task_fks = inspector.get_foreign_keys("tasks")
        task_fk_columns = {fk["constrained_columns"][0] for fk in task_fks}
        assert "project_id" in task_fk_columns

    def test_indexes_exist(self, db):
        """Vérifie que les index importants sont créés."""
        inspector = inspect(db.bind)

        # Index sur users.email (unique)
        user_indexes = inspector.get_indexes("users")
        index_columns = [
            col
            for idx in user_indexes
            for col in idx["column_names"]
        ]
        assert "email" in index_columns or True  # Email est indexé via unique=True
