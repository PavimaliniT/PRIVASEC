from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.entities import User
from app.core.rbac import get_current_user
from app.modules.simulation.scenarios import simulation_service, SCENARIOS_CATALOG

router = APIRouter(prefix="/simulation", tags=["Security Simulation Lab"])


@router.get("/scenarios")
async def list_scenarios(user: User = Depends(get_current_user)):
    """Returns catalog of pre-configured local cybersecurity attack simulation scenarios."""
    return SCENARIOS_CATALOG


@router.post("/run/{scenario_id}")
async def run_scenario(
    scenario_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Executes selected simulation scenario through the full PRIVASEC detection and defense pipeline.
    Emits real security events, computes behavioral deviation, runs Isolation Forest anomaly model,
    calculates risk, and triggers policy-driven containment.
    """
    try:
        result = await simulation_service.run_scenario(
            db=db,
            organization_id=user.organization_id,
            scenario_id=scenario_id,
            actor_pseudonym=user.pseudonym or f"sim_user_{user.id[:6]}",
            user_id=user.id
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
