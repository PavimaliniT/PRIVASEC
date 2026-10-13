from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.database import get_db
from app.models.entities import User, Anomaly, BehaviorProfile, RiskAssessment, SecurityEvent
from app.schemas.models_schema import AnomalyAnalyzeRequest, RiskEvaluateRequest
from app.core.rbac import get_current_user
from app.modules.intelligence.anomaly import anomaly_detector
from app.modules.intelligence.behavioral import behavioral_engine
from app.modules.risk.engine import risk_engine
from app.core.event_bus import emit_security_event

router = APIRouter(tags=["Intelligence & Risk Assessment"])


# Anomaly Detection Routes
@router.get("/anomalies")
async def list_anomalies(
    limit: int = 50,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Lists anomaly detection assessments across security events."""
    query = (
        select(Anomaly, SecurityEvent)
        .join(SecurityEvent, Anomaly.event_id == SecurityEvent.id)
        .where(Anomaly.organization_id == user.organization_id)
        .order_by(desc(Anomaly.created_at))
        .limit(limit)
    )
    res = await db.execute(query)
    rows = res.all()

    return [
        {
            "id": a.id,
            "event_id": a.event_id,
            "event_type": ev.event_type,
            "actor_pseudonym": ev.actor_pseudonym,
            "model_version": a.model_version,
            "anomaly_score": a.anomaly_score,
            "is_anomaly": a.is_anomaly,
            "reasons": a.reasons,
            "timestamp": a.created_at.isoformat()
        }
        for a, ev in rows
    ]


@router.post("/anomalies/analyze")
async def analyze_vector(
    req: AnomalyAnalyzeRequest,
    user: User = Depends(get_current_user)
):
    """Evaluates an arbitrary feature vector through the trained Isolation Forest model."""
    result = anomaly_detector.evaluate(req.model_dump())
    return result


@router.get("/anomalies/model-metrics")
async def get_model_metrics(user: User = Depends(get_current_user)):
    """Returns training parameters, feature importance, precision, recall, and contamination."""
    return anomaly_detector.metrics


# Behavioral Analytics Routes
@router.get("/behavior/profiles")
async def list_behavior_profiles(
    limit: int = 50,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Lists pseudonymized user activity baseline profiles."""
    query = (
        select(BehaviorProfile)
        .where(BehaviorProfile.organization_id == user.organization_id)
        .order_by(desc(BehaviorProfile.updated_at))
        .limit(limit)
    )
    res = await db.execute(query)
    profiles = res.scalars().all()
    return profiles


@router.get("/behavior/profiles/{actor_pseudonym}")
async def get_behavior_profile(
    actor_pseudonym: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Returns baseline features and activity stats for a specific pseudonymized actor."""
    profile = await behavioral_engine.get_or_create_profile(db, user.organization_id, actor_pseudonym)
    return profile


# Risk Scoring Routes
@router.post("/risk/evaluate")
async def evaluate_risk(
    req: RiskEvaluateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Computes explainable 5-factor risk score for an event."""
    result = await emit_security_event(
        db=db,
        organization_id=user.organization_id,
        actor_pseudonym=req.actor_pseudonym,
        event_type=req.event_type,
        source="risk_evaluation_console",
        severity="medium",
        metrics={
            "requests_per_minute": req.requests_per_minute,
            "failed_logins_5m": req.failed_logins_5m
        },
        device={"device_hash": "dev_eval", "recognized": req.device_novelty < 0.5},
        sensitivity=req.sensitivity,
        metadata={
            "export_volume_kb": req.export_volume_kb,
            "detected_threats": req.detected_threats
        }
    )
    return result


@router.get("/risk/events")
async def list_risk_assessments(
    limit: int = 50,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Lists computed risk assessments."""
    query = (
        select(RiskAssessment, SecurityEvent)
        .join(SecurityEvent, RiskAssessment.event_id == SecurityEvent.id)
        .where(RiskAssessment.organization_id == user.organization_id)
        .order_by(desc(RiskAssessment.created_at))
        .limit(limit)
    )
    res = await db.execute(query)
    rows = res.all()

    return [
        {
            "id": r.id,
            "event_id": r.event_id,
            "event_type": ev.event_type,
            "actor_pseudonym": ev.actor_pseudonym,
            "score": r.score,
            "level": r.level,
            "contributing_factors": r.contributing_factors,
            "recommended_action": r.recommended_action,
            "timestamp": r.created_at.isoformat()
        }
        for r, ev in rows
    ]
