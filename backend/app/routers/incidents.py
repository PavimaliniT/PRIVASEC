from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.database import get_db
from app.models.entities import User, Incident, IncidentAction, utc_now
from app.schemas.models_schema import IncidentActionRequest, IncidentResolveRequest
from app.core.rbac import get_current_user, require_roles
from app.core.audit import record_audit_event
from app.modules.response.policy_engine import response_policy_engine

router = APIRouter(prefix="/incidents", tags=["Automated Incident Response Center"])


@router.get("")
async def list_incidents(
    status_filter: Optional[str] = None,
    severity_filter: Optional[str] = None,
    limit: int = 50,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Lists security incidents with filtering by status and severity."""
    query = (
        select(Incident)
        .where(Incident.organization_id == user.organization_id)
        .order_by(desc(Incident.created_at))
        .limit(limit)
    )
    if status_filter:
        query = query.where(Incident.status == status_filter)
    if severity_filter:
        query = query.where(Incident.severity == severity_filter)

    res = await db.execute(query)
    incidents = res.scalars().all()
    return incidents


@router.get("/{incident_id}")
async def get_incident(
    incident_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves full details, timeline, and associated containment actions for an incident."""
    query = select(Incident).where(
        Incident.id == incident_id,
        Incident.organization_id == user.organization_id
    )
    res = await db.execute(query)
    incident = res.scalar_one_or_none()

    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found.")

    actions_query = select(IncidentAction).where(IncidentAction.incident_id == incident.id)
    act_res = await db.execute(actions_query)
    actions = act_res.scalars().all()

    return {
        "incident": incident,
        "actions": actions
    }


@router.post("/{incident_id}/respond")
async def execute_incident_response(
    incident_id: str,
    req: IncidentActionRequest,
    user: User = Depends(require_roles(["security_analyst", "super_admin"])),
    db: AsyncSession = Depends(get_db)
):
    """Executes an authorized containment action on an incident."""
    query = select(Incident).where(
        Incident.id == incident_id,
        Incident.organization_id == user.organization_id
    )
    res = await db.execute(query)
    incident = res.scalar_one_or_none()

    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found.")

    action = IncidentAction(
        incident_id=incident.id,
        action_type=req.action_type,
        status="EXECUTED",
        parameters={"reason": req.reason},
        approved_by=user.email,
        executed_at=utc_now()
    )
    db.add(action)

    # Update incident timeline
    tl = list(incident.timeline or [])
    tl.append({
        "timestamp": utc_now().isoformat(),
        "state": "Contained",
        "actor": user.email,
        "action": req.action_type,
        "message": f"Containment action {req.action_type} executed: {req.reason}"
    })
    incident.timeline = tl
    incident.status = "Contained"

    await db.commit()
    await db.refresh(action)

    await record_audit_event(
        db=db,
        organization_id=user.organization_id,
        actor_id=user.id,
        action="INCIDENT_CONTAINMENT_EXECUTED",
        metadata={
            "incident_id": incident.id,
            "action_type": req.action_type,
            "reason": req.reason
        }
    )

    return {"message": "Containment action executed", "action": action}


@router.post("/{incident_id}/resolve")
async def resolve_incident(
    incident_id: str,
    req: IncidentResolveRequest,
    user: User = Depends(require_roles(["security_analyst", "super_admin"])),
    db: AsyncSession = Depends(get_db)
):
    """Resolves or closes an investigated security incident."""
    query = select(Incident).where(
        Incident.id == incident_id,
        Incident.organization_id == user.organization_id
    )
    res = await db.execute(query)
    incident = res.scalar_one_or_none()

    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found.")

    incident.status = req.status
    incident.resolved_at = utc_now()
    
    tl = list(incident.timeline or [])
    tl.append({
        "timestamp": utc_now().isoformat(),
        "state": req.status,
        "actor": user.email,
        "message": f"Incident resolved: {req.resolution_note}"
    })
    incident.timeline = tl

    await db.commit()
    await db.refresh(incident)

    await record_audit_event(
        db=db,
        organization_id=user.organization_id,
        actor_id=user.id,
        action="INCIDENT_RESOLVED",
        metadata={"incident_id": incident.id, "status": req.status, "note": req.resolution_note}
    )

    return {"message": f"Incident marked as {req.status}", "incident": incident}


@router.post("/actions/{action_id}/rollback")
async def rollback_incident_action(
    action_id: str,
    user: User = Depends(require_roles(["security_analyst", "super_admin"])),
    db: AsyncSession = Depends(get_db)
):
    """Rolls back an executed containment action."""
    try:
        action = await response_policy_engine.rollback_action(db, action_id, user.id)
        return {"message": "Action rolled back successfully", "action": action}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
