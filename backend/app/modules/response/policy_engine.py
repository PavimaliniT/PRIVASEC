from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.models.entities import Incident, IncidentAction, Session, User, ApiClient, utc_now


class IncidentResponsePolicyEngine:
    async def evaluate_and_respond(
        self,
        db: AsyncSession,
        organization_id: str,
        event_id: str,
        risk_result: Dict[str, Any],
        actor_pseudonym: str,
        user_id: Optional[str] = None,
        dry_run: bool = False
    ) -> Optional[Incident]:
        """
        Evaluates risk score and triggers automated incident creation and safe containment actions.
        Threshold:
        - High risk (>=60): Creates an Incident in Triaged state.
        - Critical risk (>=80): Creates Critical Incident, executes session revocation or step-up requirement.
        """
        score = risk_result.get("score", 0.0)
        level = risk_result.get("level", "low")

        if score < 60.0:
            # Low / Medium risk: No automatic incident required
            return None

        # 1. Create Incident
        title = f"Security Incident [{level.upper()}]: Automated detection for actor {actor_pseudonym}"
        reasons = risk_result.get("reasons", [])
        
        incident = Incident(
            organization_id=organization_id,
            title=title,
            severity=level,
            status="Detected",
            risk_score=score,
            event_id=event_id,
            timeline=[
                {
                    "timestamp": utc_now().isoformat(),
                    "state": "Detected",
                    "actor": "PRIVASEC_RESPONSE_ENGINE",
                    "message": f"Threat detected with composite risk score {score}/100.",
                    "reasons": reasons
                }
            ]
        )
        db.add(incident)
        await db.commit()
        await db.refresh(incident)

        # 2. Trigger automated safe response actions
        if not dry_run:
            if score >= 80.0:
                # Critical action: Revoke active suspicious sessions if user_id known
                if user_id:
                    action = IncidentAction(
                        incident_id=incident.id,
                        action_type="REVOKE_SUSPICIOUS_SESSIONS",
                        status="EXECUTED",
                        parameters={"user_id": user_id, "reason": "Critical risk automated containment"},
                        approved_by="AUTO_POLICY_CRITICAL_RULE",
                        executed_at=utc_now()
                    )
                    db.add(action)
                    # Revoke sessions for this user
                    await db.execute(
                        update(Session)
                        .where(Session.user_id == user_id, Session.revoked_at.is_(None))
                        .values(revoked_at=utc_now())
                    )

                # Update incident state to Contained
                incident.status = "Contained"
                incident.timeline.append({
                    "timestamp": utc_now().isoformat(),
                    "state": "Contained",
                    "actor": "AUTO_POLICY_ENGINE",
                    "message": "Automated containment action executed: Active sessions invalidated."
                })
            elif score >= 60.0:
                # High action: Flag for Step-Up enforcement and notify analysts
                action = IncidentAction(
                    incident_id=incident.id,
                    action_type="REQUIRE_MFA_STEP_UP",
                    status="EXECUTED",
                    parameters={"actor": actor_pseudonym},
                    approved_by="AUTO_POLICY_HIGH_RULE",
                    executed_at=utc_now()
                )
                db.add(action)
                incident.status = "Triaged"
                incident.timeline.append({
                    "timestamp": utc_now().isoformat(),
                    "state": "Triaged",
                    "actor": "AUTO_POLICY_ENGINE",
                    "message": "Step-up MFA authentication challenge mandated for user session."
                })

            await db.commit()
            await db.refresh(incident)

        return incident

    async def rollback_action(
        self,
        db: AsyncSession,
        action_id: str,
        analyst_id: str
    ) -> IncidentAction:
        """Rolls back an executed incident containment action."""
        query = select(IncidentAction).where(IncidentAction.id == action_id)
        res = await db.execute(query)
        action = res.scalar_one_or_none()

        if not action:
            raise ValueError("Incident action not found")

        action.status = "ROLLED_BACK"
        action.rollback_at = utc_now()
        await db.commit()
        await db.refresh(action)
        return action


response_policy_engine = IncidentResponsePolicyEngine()
