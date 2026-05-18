# Configuration de l'application — chargement depuis .env via pydantic-settings
from typing import List, Optional
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Paramètres généraux
    APP_NAME: str = "Daily Management"
    APP_ENV: str = "development"
    APP_PHASE: int = 1
    DEBUG: bool = True
    SECRET_KEY: str = "changeme"
    APP_URL: str = "http://localhost:8000"

    # Base de données
    DATABASE_URL: str = "sqlite:///./daily_mgmt.db"

    # JWT
    JWT_SECRET_KEY: str = "supersecretjwtkey1234567890abcdef"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # SSO / MSAL (Phase 2)
    SSO_ENABLED: bool = False
    MSAL_CLIENT_ID: Optional[str] = None
    MSAL_CLIENT_SECRET: Optional[str] = None
    MSAL_TENANT_ID: Optional[str] = None
    MSAL_AUTHORITY: Optional[str] = "https://login.microsoftonline.com/"
    MSAL_REDIRECT_URI: Optional[str] = "http://localhost:8000/auth/sso/callback"
    MSAL_SCOPES: List[str] = ["User.Read", "openid", "profile", "email"]

    # Rapports (Phase 2)
    REPORTS_ENABLED: bool = False
    REPORTS_OUTPUT_DIR: str = "./reports_output"

    # Intégration Teams (Phase 3)
    TEAMS_ENABLED: bool = False
    TEAMS_DEFAULT_WEBHOOK_URL: Optional[str] = None
    TEAMS_NOTIFY_ON_ALERT: bool = True
    TEAMS_NOTIFY_ON_FLAG: bool = True
    TEAMS_NOTIFY_ON_DONE: bool = False
    TEAMS_WEEKLY_RECAP_CRON: str = "0 8 * * MON"

    # CORS et sécurité
    CORS_ORIGINS: List[str] = ["http://localhost:8000", "http://127.0.0.1:8000"]
    RATE_LIMIT_LOGIN: int = 5

    @field_validator("MSAL_SCOPES", "CORS_ORIGINS", mode="before")
    @classmethod
    def parse_list(cls, v):
        """Accepte une chaîne JSON ou une liste Python."""
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except Exception:
                return [v]
        return v

    @property
    def IS_SQLITE(self) -> bool:
        """Vrai si la base de données est SQLite."""
        return self.DATABASE_URL.startswith("sqlite")

    @property
    def IS_MSSQL(self) -> bool:
        """Vrai si la base de données est Microsoft SQL Server."""
        return "mssql" in self.DATABASE_URL or "pyodbc" in self.DATABASE_URL


# Instance globale des paramètres
settings = Settings()
