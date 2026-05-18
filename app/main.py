# Application FastAPI principale — Daily Management App Phase 1
import logging
from contextlib import asynccontextmanager
from datetime import date
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db, init_db
from app.models.alert import Alert
from app.models.daily_log import DailyLog
from app.models.project import Project
from app.models.task import Task
from app.models.team import Team
from app.models.user import User
from app.routers.auth import get_current_user, get_current_user_optional
from app.routers import alerts, auth, dashboard, htmx, notifications, projects, reports, tasks, team
from app.services.kpi_service import get_global_kpis
from app.services.pdca_service import get_pdca_projects_by_phase

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Rate Limiter (slowapi)
# ---------------------------------------------------------------------------
limiter = Limiter(key_func=get_remote_address)


# ---------------------------------------------------------------------------
# Lifespan — initialisation et nettoyage
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialisation de l'application au démarrage."""
    logger.info(f"Démarrage — {settings.APP_NAME} Phase {settings.APP_PHASE}")
    logger.info(f"Base de données : {settings.DATABASE_URL}")
    init_db()
    logger.info("Base de données initialisée et données de démonstration insérées.")
    yield
    logger.info("Arrêt de l'application.")


# ---------------------------------------------------------------------------
# Création de l'application FastAPI
# ---------------------------------------------------------------------------
app = FastAPI(
    title=settings.APP_NAME,
    description="Application de gestion quotidienne Lean / Visual Management — IIoT/OT",
    version="1.0.0",
    lifespan=lifespan,
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ---------------------------------------------------------------------------
# Middleware CORS
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Middleware sécurité (en-têtes HTTP)
# ---------------------------------------------------------------------------
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Ajoute les en-têtes de sécurité HTTP à toutes les réponses."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    # CSP permissif en Phase 1 (CDN requis pour Tailwind/HTMX/Alpine)
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.tailwindcss.com https://unpkg.com; "
        "style-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com https://unpkg.com; "
        "img-src 'self' data:; "
        "connect-src 'self'; "
        "font-src 'self' data:;"
    )
    if settings.APP_ENV == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


# ---------------------------------------------------------------------------
# Fichiers statiques et templates
# ---------------------------------------------------------------------------
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


# ---------------------------------------------------------------------------
# Inclusion des routeurs API
# ---------------------------------------------------------------------------
app.include_router(auth.router)
app.include_router(htmx.router)
app.include_router(dashboard.router)
app.include_router(projects.router)
app.include_router(tasks.router)
app.include_router(team.router)
app.include_router(alerts.router)
app.include_router(reports.router)
app.include_router(notifications.router)

# Route export projets (alias)
@app.get("/api/export/projects")
async def export_projects_alias(
    request: Request,
    format: str = "json",
    status: Optional[str] = None,
    team_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Alias de l'export projets pour compatibilité URL."""
    from app.routers.projects import export_projects
    return await export_projects(
        format=format,
        status=status,
        team_id=team_id,
        db=db,
        current_user=current_user,
    )


# ---------------------------------------------------------------------------
# Routes de pages (rendu HTML)
# ---------------------------------------------------------------------------

def get_flash_messages(request: Request) -> list:
    """Récupère et vide les messages flash de la session."""
    # Phase 1 : pas de vrai système de session, on utilise les query params
    messages = []
    success = request.query_params.get("success")
    error = request.query_params.get("error")
    if success:
        messages.append(("success", success))
    if error:
        messages.append(("error", error))
    return messages


@app.get("/", response_class=HTMLResponse)
async def root(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Redirige vers le dashboard si connecté, sinon vers la page de connexion."""
    if current_user:
        return RedirectResponse(url="/dashboard", status_code=302)
    return RedirectResponse(url="/login", status_code=302)


@app.get("/login", response_class=HTMLResponse)
async def login_page(
    request: Request,
    error: Optional[str] = None,
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Page de connexion."""
    if current_user:
        return RedirectResponse(url="/dashboard", status_code=302)

    return templates.TemplateResponse(
        request,
        "auth/login.html",
        {
            "error": error,
            "app_name": settings.APP_NAME,
        },
    )


@app.post("/login", response_class=HTMLResponse)
@limiter.limit(f"{settings.RATE_LIMIT_LOGIN}/5minute")
async def login_submit(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """Traitement du formulaire de connexion."""
    from app.routers.auth import verify_password, create_access_token, create_refresh_token
    from datetime import datetime

    form = await request.form()
    email = str(form.get("email", ""))
    password = str(form.get("password", ""))

    user = db.execute(select(User).where(User.email == email)).scalars().first()

    if not user or not user.hashed_password or not verify_password(password, user.hashed_password):
        return templates.TemplateResponse(
            request,
            "auth/login.html",
            {
                "error": "Email ou mot de passe incorrect",
                "email": email,
                "app_name": settings.APP_NAME,
            },
            status_code=400,
        )

    if not user.is_active:
        return templates.TemplateResponse(
            request,
            "auth/login.html",
            {
                "error": "Compte désactivé",
                "app_name": settings.APP_NAME,
            },
            status_code=403,
        )

    # Mise à jour de la dernière connexion
    user.last_login = datetime.utcnow()
    db.commit()

    # Création des tokens
    token_data = {"sub": str(user.id), "email": user.email, "role": user.role}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    # Redirection avec cookies
    redirect = RedirectResponse(url="/dashboard", status_code=302)
    redirect.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    redirect.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,
    )
    return redirect


@app.get("/logout")
async def logout(request: Request):
    """Déconnexion — supprime les cookies et redirige vers /login."""
    redirect = RedirectResponse(url="/login", status_code=302)
    redirect.delete_cookie("access_token")
    redirect.delete_cookie("refresh_token")
    return redirect


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Page tableau de bord."""
    kpi_data = get_global_kpis(db)

    # Projets PDCA
    pdca_projects = get_pdca_projects_by_phase(db)

    # Alertes actives
    active_alerts = db.execute(
        select(Alert).where(Alert.is_resolved == False).order_by(Alert.created_at.desc()).limit(8)  # noqa: E712
    ).scalars().all()

    # Projets critiques
    critical_projects = db.execute(
        select(Project).where(
            Project.is_deleted == False,  # noqa: E712
            Project.priority == "critical",
            Project.status.in_(["blocked", "in_progress"]),
        ).order_by(Project.updated_at.desc()).limit(3)
    ).scalars().all()

    # Météo humeur
    from datetime import timedelta
    from sqlalchemy import func
    seven_days_ago = date.today() - timedelta(days=7)
    team_mood_raw = db.execute(
        select(Team.id, Team.name, func.avg(DailyLog.mood_score).label("avg_mood"))
        .join(Project, Project.team_id == Team.id)
        .join(DailyLog, DailyLog.project_id == Project.id)
        .where(DailyLog.log_date >= seven_days_ago)
        .group_by(Team.id, Team.name)
    ).all()
    team_mood = {row.name: round(float(row.avg_mood), 2) for row in team_mood_raw if row.avg_mood}

    from app.schemas.dashboard import DashboardKPI
    kpis = DashboardKPI(**kpi_data)

    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "current_user": current_user,
            "kpis": kpis,
            "pdca_projects": pdca_projects,
            "active_alerts": active_alerts,
            "critical_projects": critical_projects,
            "team_mood": team_mood,
            "today": date.today().strftime("%d/%m/%Y"),
            "app_name": settings.APP_NAME,
            "flash_messages": get_flash_messages(request),
        },
    )


@app.get("/projects", response_class=HTMLResponse)
async def projects_page(
    request: Request,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    lean_phase: Optional[str] = None,
    team_id: Optional[int] = None,
    search: Optional[str] = None,
    page: int = 1,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Page liste des projets."""
    query = select(Project).where(Project.is_deleted == False)  # noqa: E712
    if status:
        query = query.where(Project.status == status)
    if priority:
        query = query.where(Project.priority == priority)
    if lean_phase:
        query = query.where(Project.lean_phase == lean_phase)
    if team_id:
        query = query.where(Project.team_id == team_id)
    if search:
        query = query.where(Project.name.ilike(f"%{search}%"))

    # Compter le total
    from sqlalchemy import func as sqlfunc
    count_query = select(sqlfunc.count()).select_from(query.subquery())
    total_count = db.execute(count_query).scalar() or 0

    page_size = 20
    total_pages = max(1, (total_count + page_size - 1) // page_size)

    projects_list = db.execute(
        query.order_by(Project.updated_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).scalars().all()

    teams = db.execute(select(Team).order_by(Team.name)).scalars().all()

    # Construire la query string pour la pagination
    filter_parts = []
    if status:
        filter_parts.append(f"status={status}")
    if priority:
        filter_parts.append(f"priority={priority}")
    if lean_phase:
        filter_parts.append(f"lean_phase={lean_phase}")
    if team_id:
        filter_parts.append(f"team_id={team_id}")
    if search:
        filter_parts.append(f"search={search}")
    filter_query = ("&" + "&".join(filter_parts)) if filter_parts else ""

    return templates.TemplateResponse(
        request,
        "projects/list.html",
        {
            "current_user": current_user,
            "projects": projects_list,
            "teams": teams,
            "total_count": total_count,
            "total_pages": total_pages,
            "current_page": page,
            "filter_query": filter_query,
            "filters": {
                "status": status, "priority": priority,
                "lean_phase": lean_phase, "team_id": team_id, "search": search,
            },
            "app_name": settings.APP_NAME,
            "flash_messages": get_flash_messages(request),
        },
    )


@app.get("/projects/{project_id}", response_class=HTMLResponse)
async def project_detail_page(
    request: Request,
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Page détail d'un projet."""
    project = db.execute(
        select(Project).where(Project.id == project_id, Project.is_deleted == False)  # noqa: E712
    ).scalars().first()

    if not project:
        raise HTTPException(status_code=404, detail="Projet introuvable")

    tasks = db.execute(
        select(Task).where(Task.project_id == project_id).order_by(Task.created_at)
    ).scalars().all()

    daily_logs = db.execute(
        select(DailyLog).where(DailyLog.project_id == project_id)
        .order_by(DailyLog.log_date.desc(), DailyLog.created_at.desc())
        .limit(20)
    ).scalars().all()

    project_alerts = db.execute(
        select(Alert).where(Alert.project_id == project_id)
        .order_by(Alert.created_at.desc())
        .limit(10)
    ).scalars().all()

    # Calcul du délai
    from app.services.lean_service import calculate_delay
    delay = calculate_delay(project)

    return templates.TemplateResponse(
        request,
        "projects/detail.html",
        {
            "current_user": current_user,
            "project": project,
            "tasks": tasks,
            "daily_logs": daily_logs,
            "project_alerts": project_alerts,
            "delay": delay,
            "today": date.today().isoformat(),
            "app_name": settings.APP_NAME,
            "flash_messages": get_flash_messages(request),
        },
    )


@app.get("/stand-up", response_class=HTMLResponse)
async def standup_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Page stand-up quotidien."""
    # Projets actifs (non terminés, non supprimés)
    active_projects = db.execute(
        select(Project).where(
            Project.is_deleted == False,  # noqa: E712
            Project.status.in_(["in_progress", "blocked", "backlog"]),
        ).order_by(Project.priority.desc(), Project.name)
    ).scalars().all()

    # Récupérer le log du jour pour chaque projet
    today = date.today()
    today_logs = {
        log.project_id: log
        for log in db.execute(
            select(DailyLog).where(DailyLog.log_date == today)
        ).scalars().all()
    }

    # Grouper les projets par responsable
    projects_by_owner: dict = {}
    for p in active_projects:
        owner_name = p.owner.username if p.owner else "Non assigné"
        if owner_name not in projects_by_owner:
            projects_by_owner[owner_name] = []
        # Attacher le log du jour au projet
        p.today_log = today_logs.get(p.id)
        projects_by_owner[owner_name].append(p)

    return templates.TemplateResponse(
        request,
        "standup.html",
        {
            "current_user": current_user,
            "projects_by_owner": projects_by_owner,
            "today": today.strftime("%d/%m/%Y"),
            "app_name": settings.APP_NAME,
        },
    )


@app.get("/team", response_class=HTMLResponse)
async def team_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Page équipe."""
    members = db.execute(select(User).order_by(User.username)).scalars().all()
    teams = db.execute(select(Team).order_by(Team.name)).scalars().all()

    # Calcul de la charge de travail (nombre de projets actifs par user)
    from sqlalchemy import func
    workload_rows = db.execute(
        select(Project.owner_id, func.count(Project.id).label("count"))
        .where(
            Project.is_deleted == False,  # noqa: E712
            Project.status.in_(["in_progress", "blocked"]),
        )
        .group_by(Project.owner_id)
    ).all()
    member_workload = {row.owner_id: row.count for row in workload_rows if row.owner_id}

    return templates.TemplateResponse(
        request,
        "team.html",
        {
            "current_user": current_user,
            "members": members,
            "teams": teams,
            "member_workload": member_workload,
            "app_name": settings.APP_NAME,
            "flash_messages": get_flash_messages(request),
        },
    )


@app.get("/reports", response_class=HTMLResponse)
async def reports_page(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """Page rapports — Phase 2."""
    return templates.TemplateResponse(
        request,
        "reports.html",
        {
            "current_user": current_user,
            "app_name": settings.APP_NAME,
        },
    )


# ---------------------------------------------------------------------------
# Routes HTMX partielles supplémentaires
# ---------------------------------------------------------------------------

@app.get("/partials/project/{project_id}/tasks", response_class=HTMLResponse)
async def partial_project_tasks(
    request: Request,
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retourne la liste des tâches d'un projet en HTML partiel."""
    tasks = db.execute(
        select(Task).where(Task.project_id == project_id).order_by(Task.created_at)
    ).scalars().all()
    project = db.execute(select(Project).where(Project.id == project_id)).scalars().first()
    return templates.TemplateResponse(
        request,
        "partials/task_item.html",
        {"tasks": tasks, "project": project, "current_user": current_user},
    )


# ---------------------------------------------------------------------------
# Healthcheck
# ---------------------------------------------------------------------------
@app.get("/health")
async def health_check():
    """Point de contrôle de santé."""
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "phase": settings.APP_PHASE,
        "env": settings.APP_ENV,
        "db_type": "sqlite" if settings.IS_SQLITE else "mssql",
    }
