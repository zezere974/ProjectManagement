# Initialisation de la base de données SQLAlchemy 2.x
import logging
from datetime import date, datetime, timedelta

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

logger = logging.getLogger(__name__)

# Arguments de connexion selon le dialecte
connect_args = {}
if settings.IS_SQLITE:
    connect_args = {"check_same_thread": False}


# Création du moteur SQLAlchemy
engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=settings.DEBUG,
)

# Session locale — utilisée comme dépendance FastAPI
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Classe de base pour tous les modèles SQLAlchemy."""
    pass


def get_db():
    """Dépendance FastAPI qui fournit une session de base de données."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Crée toutes les tables et insère les données de démonstration."""
    # Import des modèles pour que SQLAlchemy les connaisse avant create_all
    from app.models import (  # noqa: F401
        User, Team, Project, Task, DailyLog, Alert, ReportExport
    )

    Base.metadata.create_all(bind=engine)
    logger.info("Tables créées avec succès.")

    # Insertion des données de démonstration si la base est vide
    db = SessionLocal()
    try:
        from sqlalchemy import select
        result = db.execute(select(User)).first()
        if result is None:
            _seed_demo_data(db)
            logger.info("Données de démonstration insérées.")
    finally:
        db.close()


def _seed_demo_data(db) -> None:
    """Insère les données initiales pour l'environnement de démonstration IIoT/OT."""
    from passlib.context import CryptContext
    from app.models.user import User
    from app.models.team import Team
    from app.models.project import Project
    from app.models.task import Task
    from app.models.daily_log import DailyLog
    from app.models.alert import Alert

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    # --- Utilisateurs ---
    admin = User(
        email="admin@dailymgmt.local",
        username="admin",
        hashed_password=pwd_context.hash("Admin123!"),
        role="admin",
        is_active=True,
    )
    mgr_ot = User(
        email="manager.ot@dailymgmt.local",
        username="jean.martin",
        hashed_password=pwd_context.hash("Manager123!"),
        role="manager",
        is_active=True,
    )
    mgr_it = User(
        email="manager.it@dailymgmt.local",
        username="sophie.bernard",
        hashed_password=pwd_context.hash("Manager123!"),
        role="manager",
        is_active=True,
    )
    u1 = User(
        email="ingenieur1@dailymgmt.local",
        username="pierre.dubois",
        hashed_password=pwd_context.hash("Member123!"),
        role="member",
        is_active=True,
    )
    u2 = User(
        email="ingenieur2@dailymgmt.local",
        username="marie.leroy",
        hashed_password=pwd_context.hash("Member123!"),
        role="member",
        is_active=True,
    )
    u3 = User(
        email="analyste@dailymgmt.local",
        username="thomas.petit",
        hashed_password=pwd_context.hash("Member123!"),
        role="member",
        is_active=True,
    )
    u4 = User(
        email="chef.projet@dailymgmt.local",
        username="camille.moreau",
        hashed_password=pwd_context.hash("Member123!"),
        role="member",
        is_active=True,
    )
    u5 = User(
        email="technicien@dailymgmt.local",
        username="lucas.simon",
        hashed_password=pwd_context.hash("Member123!"),
        role="member",
        is_active=True,
    )

    db.add_all([admin, mgr_ot, mgr_it, u1, u2, u3, u4, u5])
    db.flush()

    # --- Équipes ---
    team_ot = Team(
        name="Cybersécurité OT",
        description="Équipe en charge de la cybersécurité des systèmes opérationnels",
        manager_id=mgr_ot.id,
        color_code="#ef4444",
    )
    team_it = Team(
        name="Infrastructure IT",
        description="Équipe responsable de l'infrastructure informatique",
        manager_id=mgr_it.id,
        color_code="#3b82f6",
    )
    db.add_all([team_ot, team_it])
    db.flush()

    today = date.today()

    # --- Projets ---
    p1 = Project(
        name="Déploiement Firewall OT Niveau 2",
        description="Déploiement et configuration des pare-feux industriels sur le réseau OT niveau 2 selon IEC 62443.",
        team_id=team_ot.id,
        status="in_progress",
        priority="critical",
        lean_phase="do",
        owner_id=mgr_ot.id,
        start_date=today - timedelta(days=30),
        target_date=today + timedelta(days=15),
        progress_pct=65,
        kpi_target=100.0,
        kpi_actual=65.0,
        kpi_unit="%",
        is_flagged=False,
    )
    p2 = Project(
        name="Migration SCADA v3→v4",
        description="Migration de la plateforme SCADA vers la version 4 avec maintien de la continuité opérationnelle.",
        team_id=team_ot.id,
        status="blocked",
        priority="high",
        lean_phase="plan",
        owner_id=u1.id,
        start_date=today - timedelta(days=45),
        target_date=today + timedelta(days=60),
        progress_pct=20,
        kpi_target=100.0,
        kpi_actual=20.0,
        kpi_unit="%",
        is_flagged=True,
        notes="Bloqué en attente de validation fournisseur.",
    )
    p3 = Project(
        name="Certification IEC 62443",
        description="Obtention de la certification IEC 62443-2-4 pour les systèmes de contrôle industriel.",
        team_id=team_ot.id,
        status="in_progress",
        priority="high",
        lean_phase="check",
        owner_id=u3.id,
        start_date=today - timedelta(days=90),
        target_date=today + timedelta(days=20),
        progress_pct=80,
        kpi_target=100.0,
        kpi_actual=80.0,
        kpi_unit="%",
    )
    p4 = Project(
        name="Audit NIS2 Conformité",
        description="Mise en conformité avec la directive NIS2 — évaluation des écarts et plan d'action.",
        team_id=team_ot.id,
        status="in_progress",
        priority="critical",
        lean_phase="act",
        owner_id=mgr_ot.id,
        start_date=today - timedelta(days=20),
        target_date=today + timedelta(days=40),
        progress_pct=45,
        kpi_target=100.0,
        kpi_actual=45.0,
        kpi_unit="%",
    )
    p5 = Project(
        name="Déploiement Capteurs IoT Atelier",
        description="Installation de 120 capteurs IoT dans l'atelier de production pour monitoring en temps réel.",
        team_id=team_it.id,
        status="in_progress",
        priority="medium",
        lean_phase="do",
        owner_id=u4.id,
        start_date=today - timedelta(days=15),
        target_date=today + timedelta(days=30),
        progress_pct=55,
        kpi_target=120.0,
        kpi_actual=66.0,
        kpi_unit="capteurs",
    )
    p6 = Project(
        name="Mise à Jour HMI Production",
        description="Mise à jour des interfaces homme-machine (HMI) sur les lignes de production 1 à 4.",
        team_id=team_it.id,
        status="backlog",
        priority="medium",
        lean_phase="plan",
        owner_id=mgr_it.id,
        start_date=today + timedelta(days=10),
        target_date=today + timedelta(days=90),
        progress_pct=0,
        kpi_target=4.0,
        kpi_actual=0.0,
        kpi_unit="lignes",
    )
    p7 = Project(
        name="Intégration OPC-UA → MES",
        description="Intégration du protocole OPC-UA avec le système d'exécution de fabrication (MES).",
        team_id=team_it.id,
        status="in_progress",
        priority="high",
        lean_phase="do",
        owner_id=u2.id,
        start_date=today - timedelta(days=10),
        target_date=today + timedelta(days=50),
        progress_pct=30,
        kpi_target=100.0,
        kpi_actual=30.0,
        kpi_unit="%",
    )
    p8 = Project(
        name="Plan de Continuité d'Activité OT",
        description="Rédaction et validation du plan de continuité d'activité pour les systèmes OT critiques.",
        team_id=team_ot.id,
        status="done",
        priority="high",
        lean_phase="act",
        owner_id=u5.id,
        start_date=today - timedelta(days=60),
        target_date=today - timedelta(days=5),
        actual_end_date=today - timedelta(days=7),
        progress_pct=100,
        kpi_target=100.0,
        kpi_actual=100.0,
        kpi_unit="%",
    )

    db.add_all([p1, p2, p3, p4, p5, p6, p7, p8])
    db.flush()

    # --- Tâches ---
    tasks = [
        Task(project_id=p1.id, assigned_to_id=u1.id, title="Définir les règles de filtrage réseau", status="done"),
        Task(project_id=p1.id, assigned_to_id=u1.id, title="Installer les appliances firewall", status="in_progress"),
        Task(project_id=p1.id, assigned_to_id=u3.id, title="Tester la connectivité OT post-firewall", status="todo"),
        Task(project_id=p1.id, assigned_to_id=mgr_ot.id, title="Valider avec l'équipe production", status="todo"),

        Task(project_id=p2.id, assigned_to_id=u1.id, title="Analyser les incompatibilités v3/v4", status="done"),
        Task(project_id=p2.id, assigned_to_id=u4.id, title="Obtenir validation fournisseur SCADA", status="blocked"),
        Task(project_id=p2.id, assigned_to_id=u1.id, title="Préparer environnement de test", status="todo", is_quick_win=True),

        Task(project_id=p3.id, assigned_to_id=u3.id, title="Préparer la documentation technique", status="done"),
        Task(project_id=p3.id, assigned_to_id=u3.id, title="Réaliser l'audit interne", status="done"),
        Task(project_id=p3.id, assigned_to_id=mgr_ot.id, title="Soumettre dossier auditeur externe", status="in_progress"),

        Task(project_id=p4.id, assigned_to_id=mgr_ot.id, title="Cartographier les actifs critiques", status="done"),
        Task(project_id=p4.id, assigned_to_id=u3.id, title="Analyser les écarts NIS2", status="in_progress"),
        Task(project_id=p4.id, assigned_to_id=u4.id, title="Rédiger le plan d'action correctif", status="todo"),

        Task(project_id=p5.id, assigned_to_id=u4.id, title="Commander les capteurs IoT", status="done"),
        Task(project_id=p5.id, assigned_to_id=u5.id, title="Câbler les capteurs zone A", status="done"),
        Task(project_id=p5.id, assigned_to_id=u5.id, title="Câbler les capteurs zone B", status="in_progress"),
        Task(project_id=p5.id, assigned_to_id=u2.id, title="Configurer le collecteur de données", status="todo", is_quick_win=True),

        Task(project_id=p6.id, assigned_to_id=mgr_it.id, title="Inventorier les HMI existants", status="todo"),
        Task(project_id=p6.id, assigned_to_id=u2.id, title="Valider compatibilité logicielle", status="todo"),

        Task(project_id=p7.id, assigned_to_id=u2.id, title="Installer le serveur OPC-UA", status="done"),
        Task(project_id=p7.id, assigned_to_id=u2.id, title="Mapper les tags OPC-UA vers MES", status="in_progress"),
        Task(project_id=p7.id, assigned_to_id=mgr_it.id, title="Tester les flux de données", status="todo"),

        Task(project_id=p8.id, assigned_to_id=u5.id, title="Identifier les processus critiques", status="done"),
        Task(project_id=p8.id, assigned_to_id=u5.id, title="Rédiger le PCA OT", status="done"),
        Task(project_id=p8.id, assigned_to_id=mgr_ot.id, title="Valider et faire signer le PCA", status="done"),
    ]
    db.add_all(tasks)
    db.flush()

    # --- Journaux quotidiens (5 derniers jours) ---
    daily_logs = []
    for delta in range(5, 0, -1):
        log_date = today - timedelta(days=delta)
        daily_logs.extend([
            DailyLog(
                project_id=p1.id,
                user_id=u1.id,
                log_date=log_date,
                what_done="Configuration des règles de filtrage sur la zone DMZ OT.",
                what_planned="Finaliser la configuration et lancer les tests de connectivité.",
                blockers="Accès restreint à certains équipements en heures de production.",
                mood_score=4,
            ),
            DailyLog(
                project_id=p2.id,
                user_id=u1.id,
                log_date=log_date,
                what_done="Relance du fournisseur par email et appel téléphonique.",
                what_planned="Attente retour fournisseur — préparer environnement de test en parallèle.",
                blockers="Fournisseur SCADA n'a pas encore transmis la documentation de migration.",
                mood_score=2,
            ),
            DailyLog(
                project_id=p5.id,
                user_id=u4.id,
                log_date=log_date,
                what_done=f"Câblage de {delta * 3} capteurs supplémentaires en zone B.",
                what_planned="Poursuivre le câblage et commencer la configuration réseau.",
                blockers=None,
                mood_score=4,
            ),
        ])
    db.add_all(daily_logs)
    db.flush()

    # --- Alertes ---
    alerts = [
        Alert(
            project_id=p2.id,
            created_by_id=mgr_ot.id,
            type="blocker",
            message="Migration SCADA bloquée depuis plus de 5 jours — validation fournisseur en attente.",
            is_resolved=False,
            teams_notified=False,
        ),
        Alert(
            project_id=p1.id,
            created_by_id=u1.id,
            type="delay",
            message="Risque de dépassement de la date cible si les tests ne démarrent pas cette semaine.",
            is_resolved=False,
            teams_notified=False,
        ),
        Alert(
            project_id=p7.id,
            created_by_id=mgr_it.id,
            type="resource",
            message="Manque de ressources OPC-UA — un expert supplémentaire est nécessaire.",
            is_resolved=False,
            teams_notified=False,
        ),
    ]
    db.add_all(alerts)
    db.commit()
    logger.info("Données de démonstration IIoT/OT insérées avec succès.")
