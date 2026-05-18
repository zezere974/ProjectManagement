# Initialisation du package schémas Pydantic v2
from app.schemas.user import UserBase, UserCreate, UserUpdate, UserResponse, Token, TokenData
from app.schemas.team import TeamBase, TeamCreate, TeamUpdate, TeamResponse
from app.schemas.project import ProjectBase, ProjectCreate, ProjectUpdate, ProjectResponse, ProjectDetail
from app.schemas.task import TaskBase, TaskCreate, TaskUpdate, TaskResponse
from app.schemas.daily_log import DailyLogBase, DailyLogCreate, DailyLogResponse
from app.schemas.alert import AlertBase, AlertCreate, AlertResponse
from app.schemas.dashboard import DashboardKPI, DashboardResponse

__all__ = [
    "UserBase", "UserCreate", "UserUpdate", "UserResponse", "Token", "TokenData",
    "TeamBase", "TeamCreate", "TeamUpdate", "TeamResponse",
    "ProjectBase", "ProjectCreate", "ProjectUpdate", "ProjectResponse", "ProjectDetail",
    "TaskBase", "TaskCreate", "TaskUpdate", "TaskResponse",
    "DailyLogBase", "DailyLogCreate", "DailyLogResponse",
    "AlertBase", "AlertCreate", "AlertResponse",
    "DashboardKPI", "DashboardResponse",
]
