# Routeur notifications Teams — Phase 3 (retourne 501 en Phase 1)
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/notifications", tags=["Notifications (Phase 3)"])


@router.post("/teams/test")
async def test_teams():
    """Test de connexion Teams — disponible en Phase 3."""
    raise HTTPException(status_code=501, detail="Disponible en Phase 3")


@router.post("/teams/alert/{alert_id}")
async def send_alert_to_teams(alert_id: int):
    """Envoi d'alerte vers Teams — disponible en Phase 3."""
    raise HTTPException(status_code=501, detail="Disponible en Phase 3")


@router.post("/teams/weekly-recap")
async def send_weekly_recap():
    """Récapitulatif hebdomadaire Teams — disponible en Phase 3."""
    raise HTTPException(status_code=501, detail="Disponible en Phase 3")
