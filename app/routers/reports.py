# Routeur rapports — Phase 2 (retourne 501 en Phase 1)
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/reports", tags=["Rapports (Phase 2)"])


@router.get("/weekly")
async def weekly_report():
    """Rapport hebdomadaire — disponible en Phase 2."""
    raise HTTPException(status_code=501, detail="Disponible en Phase 2")


@router.get("/monthly")
async def monthly_report():
    """Rapport mensuel — disponible en Phase 2."""
    raise HTTPException(status_code=501, detail="Disponible en Phase 2")


@router.get("/project/{project_id}")
async def project_report(project_id: int):
    """Rapport de projet — disponible en Phase 2."""
    raise HTTPException(status_code=501, detail="Disponible en Phase 2")


@router.get("/team-kpi")
async def team_kpi_report():
    """Rapport KPI équipe — disponible en Phase 2."""
    raise HTTPException(status_code=501, detail="Disponible en Phase 2")
