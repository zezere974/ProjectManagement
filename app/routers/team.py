# Routeur équipe — gestion des membres et des équipes
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.team import Team
from app.routers.auth import get_current_user, hash_password, require_role
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.schemas.team import TeamCreate, TeamResponse, TeamUpdate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/team", tags=["Équipe"])


@router.get("", response_model=list[UserResponse])
async def get_team_members(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retourne la liste de tous les membres de l'équipe."""
    users = db.execute(select(User).order_by(User.username)).scalars().all()
    return users


@router.get("/teams", response_model=list[TeamResponse])
async def get_teams(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retourne la liste de toutes les équipes."""
    teams = db.execute(select(Team).order_by(Team.name)).scalars().all()
    return teams


@router.post("/teams", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
async def create_team(
    team_data: TeamCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"])),
):
    """Crée une nouvelle équipe. Réservé aux admins."""
    team = Team(**team_data.model_dump())
    db.add(team)
    db.commit()
    db.refresh(team)
    logger.info(f"Équipe créée : {team.name} par {current_user.email}")
    return team


@router.post("/members", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def add_member(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager"])),
):
    """Ajoute un nouveau membre. Réservé aux admins et managers."""
    # Vérifier l'unicité de l'email
    existing = db.execute(
        select(User).where(User.email == user_data.email)
    ).scalars().first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Un utilisateur avec cet email existe déjà",
        )

    # Vérifier l'unicité du username
    existing_username = db.execute(
        select(User).where(User.username == user_data.username)
    ).scalars().first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ce nom d'utilisateur est déjà pris",
        )

    # Les managers ne peuvent créer que des membres
    if current_user.role == "manager" and user_data.role in ("admin", "manager"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Les managers ne peuvent créer que des membres",
        )

    user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=hash_password(user_data.password),
        role=user_data.role,
        is_active=user_data.is_active,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info(f"Membre ajouté : {user.email} par {current_user.email}")
    return user


@router.put("/members/{user_id}", response_model=UserResponse)
async def update_member(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager"])),
):
    """Met à jour un membre. Réservé aux admins et managers."""
    user = db.execute(select(User).where(User.id == user_id)).scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    # Les managers ne peuvent pas modifier les admins ou autres managers
    if current_user.role == "manager" and user.role in ("admin", "manager"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Modification non autorisée",
        )

    update_data = user_data.model_dump(exclude_unset=True)

    if "password" in update_data and update_data["password"]:
        update_data["hashed_password"] = hash_password(update_data.pop("password"))
    else:
        update_data.pop("password", None)

    for field, value in update_data.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)
    logger.info(f"Membre mis à jour : {user.email} par {current_user.email}")
    return user


@router.delete("/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_member(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"])),
):
    """
    Désactive un membre (is_active=False).
    Suppression logique uniquement — réservé aux admins.
    """
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossible de désactiver votre propre compte",
        )

    user = db.execute(select(User).where(User.id == user_id)).scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    user.is_active = False
    db.commit()
    logger.info(f"Membre désactivé : {user.email} par {current_user.email}")
