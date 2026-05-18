# Configuration Alembic — import des modèles et support render_as_batch pour SQLite
import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Ajouter le répertoire racine du projet au chemin Python
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import de la configuration de l'application
from app.config import settings

# Import de tous les modèles pour que SQLAlchemy les enregistre dans le métadata
from app.database import Base
from app.models import User, Team, Project, Task, DailyLog, Alert, ReportExport  # noqa: F401

# Objet de configuration Alembic
config = context.config

# Utiliser la DATABASE_URL depuis les paramètres de l'application
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Configuration des loggers depuis le fichier .ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Métadata cible pour la génération automatique des migrations
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Exécute les migrations en mode 'offline'.
    Configure le contexte avec l'URL de la base de données uniquement.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        # render_as_batch=True est requis pour SQLite (ALTER TABLE simulé)
        render_as_batch=settings.IS_SQLITE,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Exécute les migrations en mode 'online'.
    Crée un moteur SQLAlchemy et l'associe au contexte.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        # Arguments spécifiques à SQLite
        connect_args={"check_same_thread": False} if settings.IS_SQLITE else {},
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # render_as_batch=True permet les migrations ALTER TABLE sur SQLite
            render_as_batch=settings.IS_SQLITE,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
