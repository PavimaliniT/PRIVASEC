from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.entities import SecurityEvent, Anomaly, RiskAssessment, utc_now
from app.modules.intelligence.behavioral import behavioral_engine
from app.modules.intelligence.anomaly import anomaly_detector
from app.modules.risk.engine import risk_engine
from app.modules.response.policy_engine import response_policy_engine
from app.core.audit import record_audit_event


async def emit_security_event(
    db: AsyncSession,
    organization_id: str,
    actor_pseudonym: str,
    event_type: str,
    source: str = "gateway",
    severity: str = "low",
    network: Optional[Dict[str, Any]] = None,
    device: Optional[Dict[str, Any]] = None,
    metrics: Optional[Dict[str, Any]] = None,
    sensitivity: str = "low",
    metadata: Optional[Dict[str, Any]] = None,
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Core PRIVASEC Normalized Event Pipeline:
    Ingests event -> Computes behavioral deviations -> Evaluates ML anomaly score ->
    Calculates 5-factor explainable risk score -> Triggers automated incident response policies ->
    Appends audit log if significant.
    """
    network_meta = network or {"ip_token": "ip_internal", "country_code": "IN"}
    device_meta = device or {"device_hash": "dev_standard", "recognized": True}
    metrics_meta = metrics or {"requests_per_minute": 15.0, "failed_logins_5m": 0}
    metadata_clean = metadata or {}

    # 1. Persist Normalized Security Event
    event = SecurityEvent(
        organization_id=organization_id,
        actor_pseudonym=actor_pseudonym,
        event_type=event_type,
        severity=severity,
        source=source,
        network_meta=network_meta,
        device_meta=device_meta,
        metrics=metrics_meta,
        metadata_redacted=metadata_clean,
        sensitivity=sensitivity,
        timestamp=utc_now()
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)

    # 2. Behavioral Baseline Analytics
    profile = await behavioral_engine.get_or_create_profile(db, organization_id, actor_pseudonym)
    behavior_signals = behavioral_engine.compute_deviations(
        profile,
        {"device": device_meta, "metrics": metrics_meta}
    )
    # Adapt baseline in background
    await behavioral_engine.update_baseline(
        db,
        profile,
        {"device": device_meta, "metrics": metrics_meta}
    )

    # 3. ML Anomaly Detection (Isolation Forest)
    feature_vector = {
        "requests_per_minute": metrics_meta.get("requests_per_minute", 15.0),
        "failed_logins_5m": metrics_meta.get("failed_logins_5m", 0),
        "time_of_day_deviation": behavior_signals.get("time_of_day_deviation", 0.0),
        "device_novelty": behavior_signals.get("device_novelty", 0.0),
        "endpoint_rarity": metadata_clean.get("endpoint_rarity", 0.1),
        "export_volume_kb": metadata_clean.get("export_volume_kb", 0.0),
        "access_denial_frequency": metrics_meta.get("access_denials_5m", 0)
    }
    ml_result = anomaly_detector.evaluate(feature_vector)

    anomaly_record = Anomaly(
        organization_id=organization_id,
        event_id=event.id,
        model_version=ml_result["model_version"],
        anomaly_score=ml_result["anomaly_score"],
        is_anomaly=ml_result["is_anomaly"],
        reasons=ml_result["reasons"]
    )
    db.add(anomaly_record)

    # 4. Composite Risk Evaluation
    auth_signals = {
        "failed_logins_5m": metrics_meta.get("failed_logins_5m", 0),
        "credential_stuffing_suspected": "CREDENTIAL_STUFFING" in event_type or metrics_meta.get("failed_logins_5m", 0) >= 5
    }
    api_signals = {
        "detected_threats": metadata_clean.get("detected_threats", []),
        "rate_limited": "RATE_LIMIT" in event_type or metrics_meta.get("requests_per_minute", 0) > 100
    }
    sensitivity_signals = {
        "sensitivity": sensitivity,
        "export_volume_kb": metadata_clean.get("export_volume_kb", 0.0)
    }

    risk_result = risk_engine.calculate_risk(
        auth_signals=auth_signals,
        behavioral_signals=behavior_signals,
        ml_signals=ml_result,
        api_signals=api_signals,
        data_sensitivity_signals=sensitivity_signals
    )

    risk_record = RiskAssessment(
        organization_id=organization_id,
        event_id=event.id,
        score=risk_result["score"],
        level=risk_result["level"],
        contributing_factors=risk_result["contributing_factors"],
        recommended_action=risk_result["recommended_action"]
    )
    db.add(risk_record)
    await db.commit()

    # 5. Automated Incident Response Policy
    incident = await response_policy_engine.evaluate_and_respond(
        db=db,
        organization_id=organization_id,
        event_id=event.id,
        risk_result=risk_result,
        actor_pseudonym=actor_pseudonym,
        user_id=user_id
    )

    # 6. Audit Trail for Elevated Threat Detections
    if risk_result["score"] >= 60.0:
        await record_audit_event(
            db=db,
            organization_id=organization_id,
            actor_id=actor_pseudonym,
            action=f"SECURITY_ALERT_{risk_result['level'].upper()}",
            metadata={
                "event_id": event.id,
                "event_type": event_type,
                "risk_score": risk_result["score"],
                "incident_created": incident.id if incident else None,
                "reasons": risk_result["reasons"]
            }
        )

    return {
        "event_id": event.id,
        "organization_id": organization_id,
        "actor_pseudonym": actor_pseudonym,
        "event_type": event_type,
        "source": source,
        "timestamp": event.timestamp.isoformat(),
        "network": network_meta,
        "device": device_meta,
        "metrics": metrics_meta,
        "sensitivity": sensitivity,
        "anomaly": {
            "score": ml_result["anomaly_score"],
            "is_anomaly": ml_result["is_anomaly"],
            "reasons": ml_result["reasons"]
        },
        "behavior": {
            "deviation_score": behavior_signals["deviation_score"],
            "device_novelty": behavior_signals["device_novelty"],
            "time_deviation": behavior_signals["time_of_day_deviation"]
        },
        "risk": {
            "score": risk_result["score"],
            "level": risk_result["level"],
            "recommended_action": risk_result["recommended_action"],
            "reasons": risk_result["reasons"],
            "factors": risk_result["contributing_factors"]
        },
        "incident_id": incident.id if incident else None
    }
