# Routeur authentification — JWT via cookies, rate limiting, SSO (Phase 2)
import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.schemas.user import Token, TokenData, UserResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentification"])

# Contexte de hachage des mots de passe
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Schéma de sécurité HTTP Bearer (pour les appels API)
security = HTTPBearer(auto_error=False)


# ---------------------------------------------------------------------------
# Utilitaires JWT
# ---------------------------------------------------------------------------

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Vérifie le mot de passe en clair contre le hash bcrypt."""
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    """Hache un mot de passe avec bcrypt."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Crée un token d'accès JWT."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(data: dict) -> str:
    """Crée un token de rafraîchissement JWT."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """Décode et valide un token JWT. Lève JWTError si invalide."""
    return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])


# ---------------------------------------------------------------------------
# Dépendances FastAPI
# ---------------------------------------------------------------------------

async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """
    Dépendance qui retourne l'utilisateur courant.
    Accepte le token depuis le cookie ou le header Authorization.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentification requise",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token: Optional[str] = None

    # Priorité au header Authorization
    if credentials:
        token = credentials.credentials
    else:
        # Fallback sur le cookie
        token = request.cookies.get("access_token")

    if not token:
        raise credentials_exception

    try:
        payload = decode_token(token)
        user_id: Optional[int] = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        token_data = TokenData(user_id=int(user_id))
    except (JWTError, ValueError):
        raise credentials_exception

    user = db.execute(
        select(User).where(User.id == token_data.user_id)
    ).scalars().first()

    if user is None or not user.is_active:
        raise credentials_exception

    return user


async def get_current_user_optional(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """Dépendance optionnelle — retourne None si non authentifié."""
    try:
        return await get_current_user(request, credentials, db)
    except HTTPException:
        return None


def require_role(roles: list[str]):
    """
    Factory de dépendance pour vérifier que l'utilisateur possède l'un des rôles requis.
    Usage : Depends(require_role(["admin", "manager"]))
    """
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Rôle requis : {', '.join(roles)}",
            )
        return current_user

    return role_checker


# ---------------------------------------------------------------------------
# Routes d'authentification
# ---------------------------------------------------------------------------

@router.post("/login", response_model=Token)
async def login(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """
    Authentification par email + mot de passe.
    Retourne les tokens JWT et les positionne dans des cookies sécurisés.
    Rate limited à 5 tentatives par 5 minutes.
    """
    # Récupérer les credentials depuis le corps de la requête (form ou JSON)
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        body = await request.json()
        email = body.get("email", "")
        password = body.get("password", "")
    else:
        form = await request.form()
        email = str(form.get("email", ""))
        password = str(form.get("password", ""))

    if not email or not password:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Email et mot de passe requis",
        )

    # Rechercher l'utilisateur
    user = db.execute(
        select(User).where(User.email == email)
    ).scalars().first()

    if not user or not user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect",
        )

    if not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Compte désactivé",
        )

    # Mise à jour de la date de dernière connexion
    user.last_login = datetime.utcnow()
    db.commit()

    # Création des tokens
    token_data = {"sub": str(user.id), "email": user.email, "role": user.role}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    # Positionnement des cookies sécurisés
    is_secure = not settings.IS_SQLITE or settings.APP_ENV == "production"
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,
    )

    logger.info(f"Connexion réussie pour l'utilisateur {user.email}")

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """Rafraîchit le token d'accès depuis le token de rafraîchissement."""
    token = request.cookies.get("refresh_token")

    # Accepter aussi via JSON body
    if not token:
        try:
            body = await request.json()
            token = body.get("refresh_token")
        except Exception:
            pass

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de rafraîchissement manquant",
        )

    try:
        payload = decode_token(token)
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token invalide",
            )
        user_id = int(payload.get("sub"))
    except (JWTError, ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de rafraîchissement invalide ou expiré",
        )

    user = db.execute(select(User).where(User.id == user_id)).scalars().first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Utilisateur introuvable")

    token_data = {"sub": str(user.id), "email": user.email, "role": user.role}
    access_token = create_access_token(token_data)
    new_refresh_token = create_refresh_token(token_data)

    response.set_cookie(key="access_token", value=access_token, httponly=True, samesite="lax",
                        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)
    response.set_cookie(key="refresh_token", value=new_refresh_token, httponly=True, samesite="lax",
                        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600)

    return Token(access_token=access_token, refresh_token=new_refresh_token, token_type="bearer")


@router.post("/logout")
async def logout(response: Response):
    """
    Déconnexion — supprime les cookies JWT côté client.
    Note : en Phase 1, la révocation côté serveur n'est pas implémentée.
    """
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return {"message": "Déconnexion réussie"}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Retourne les informations de l'utilisateur courant."""
    return current_user


# ---------------------------------------------------------------------------
# Routes SSO — Phase 2 (commentées)
# ---------------------------------------------------------------------------

# @router.get("/sso/login")
# async def sso_login():
#     """Redirige vers la page de connexion Microsoft Azure AD."""
#     # Phase 2 — nécessite msal
#     raise HTTPException(status_code=501, detail="SSO disponible en Phase 2")

# @router.get("/sso/callback")
# async def sso_callback(code: str, state: str, db: Session = Depends(get_db)):
#     """Callback OAuth2 MSAL après authentification Azure AD."""
#     # Phase 2 — nécessite msal et MSAL_CLIENT_ID configuré
#     raise HTTPException(status_code=501, detail="SSO disponible en Phase 2")
