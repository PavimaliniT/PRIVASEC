import logging
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.entities import (
    Organization, Role, User, PrivacyPolicy, SecurityEvent, Incident,
    Anomaly, RiskAssessment, AuditLog, BehaviorProfile, utc_now
)
from app.core.security import hash_password
from app.core.audit import record_audit_event
from app.modules.privacy.pii_detector import pii_detector

logger = logging.getLogger("privasec.seed")


async def seed_database(db: AsyncSession):
    """Seeds database with default organization, roles, users, and baseline records."""
    # Check if already seeded
    res = await db.execute(select(Organization).limit(1))
    if res.scalar_one_or_none():
        return

    logger.info("Initializing PRIVASEC initial database seed...")

    # 1. Default Organization
    org = Organization(
        name="PRIVASEC Cyber Defense SOC",
        settings={"retention_days": 90, "mfa_enforced": False, "simulation_mode": True}
    )
    db.add(org)
    await db.commit()
    await db.refresh(org)

    # 2. Roles
    roles_def = [
        ("super_admin", ["all", "manage_users", "manage_policies", "reidentify", "rotate_keys"]),
        ("security_analyst", ["read_events", "investigate_anomalies", "contain_incidents", "run_simulations"]),
        ("privacy_officer", ["manage_privacy", "reidentify", "review_pii", "audit_retention"]),
        ("standard_user", ["access_crypto_lab", "read_self"])
    ]
    created_roles = {}
    for r_name, perms in roles_def:
        role = Role(organization_id=org.id, name=r_name, permissions=perms)
        db.add(role)
        created_roles[r_name] = role

    await db.commit()
    for r in created_roles.values():
        await db.refresh(r)

    # 3. Seed Users (All use Password123!)
    default_pw_hash = hash_password("Password123!")
    users_def = [
        ("admin@privasec.io", "super_admin", "usr_admin_001"),
        ("analyst@privasec.io", "security_analyst", "usr_analyst_001"),
        ("privacy@privasec.io", "privacy_officer", "usr_privacy_001"),
        ("user@privasec.io", "standard_user", "usr_standard_001")
    ]
    created_users = {}
    for email, role_name, pseudonym in users_def:
        user = User(
            organization_id=org.id,
            email=email,
            password_hash=default_pw_hash,
            role_id=created_roles[role_name].id,
            pseudonym=pseudonym,
            mfa_enabled=False
        )
        db.add(user)
        created_users[email] = user

    await db.commit()
    for u in created_users.values():
        await db.refresh(u)

    # 4. Default Privacy Policies
    policies = [
        ("EMAIL_ADDRESS", "MASK", "PARTIAL", 90),
        ("PHONE_NUMBER", "MASK", "PARTIAL", 90),
        ("PAN_NUMBER", "MASK", "PARTIAL", 180),
        ("AADHAAR_NUMBER", "MASK", "PARTIAL", 180),
        ("CREDIT_CARD", "REDACT", "REDACT", 30),
        ("SECRET_KEY", "REDACT", "REDACT", 7)
    ]
    for entity_type, trans, strat, ret in policies:
        pol = PrivacyPolicy(
            organization_id=org.id,
            entity_type=entity_type,
            transformation=trans,
            masking_strategy=strat,
            retention_days=ret,
            is_active=True
        )
        db.add(pol)

    # 5. Baseline Behavioral Profiles
    for u in created_users.values():
        bp = BehaviorProfile(
            organization_id=org.id,
            actor_pseudonym=u.pseudonym,
            baseline_features={
                "known_devices": ["dev_standard_chrome_desktop"],
                "typical_hours": [9, 10, 11, 12, 13, 14, 15, 16, 17, 18],
                "avg_requests_per_min": 18.5,
                "std_requests_per_min": 4.2,
                "total_events_observed": 45,
                "last_active": utc_now().isoformat()
            },
            recent_activity=[]
        )
        db.add(bp)

    await db.commit()

    # 6. Seed Realistic Initial Security Events & Incidents
    now = utc_now()
    events_data = [
        (
            "AUTH_LOGIN_SUCCESS", "low", "usr_admin_001",
            {"ip_token": "ip_tok_office_1", "country_code": "IN"},
            {"device_hash": "dev_standard_chrome_desktop", "recognized": True},
            {"requests_per_minute": 14.0, "failed_logins_5m": 0},
            22.0, "low"
        ),
        (
            "API_ANOMALY_BURST", "high", "usr_unknown_external",
            {"ip_token": "ip_tok_scanner_09", "country_code": "NL"},
            {"device_hash": "dev_curl_bot", "recognized": False},
            {"requests_per_minute": 190.0, "failed_logins_5m": 0},
            72.5, "high"
        ),
        (
            "AUTH_BRUTE_FORCE_FAILURE", "critical", "usr_target_01",
            {"ip_token": "ip_tok_malicious_proxy", "country_code": "RO"},
            {"device_hash": "dev_headless_cluster", "recognized": False},
            {"requests_per_minute": 95.0, "failed_logins_5m": 9},
            88.0, "critical"
        ),
        (
            "PRIVACY_PII_SCAN_EXECUTED", "low", "usr_privacy_001",
            {"ip_token": "ip_tok_office_1", "country_code": "IN"},
            {"device_hash": "dev_standard_chrome_desktop", "recognized": True},
            {"requests_per_minute": 16.0, "failed_logins_5m": 0},
            18.0, "low"
        )
    ]

    for ev_type, sev, actor, net, dev, met, r_score, r_level in events_data:
        ev = SecurityEvent(
            organization_id=org.id,
            actor_pseudonym=actor,
            event_type=ev_type,
            severity=sev,
            source="seed",
            network_meta=net,
            device_meta=dev,
            metrics=met,
            metadata_redacted={"seeded": True},
            timestamp=now - timedelta(minutes=15)
        )
        db.add(ev)
        await db.commit()
        await db.refresh(ev)

        # Add Risk Assessment
        ra = RiskAssessment(
            organization_id=org.id,
            event_id=ev.id,
            score=r_score,
            level=r_level,
            contributing_factors={"auth": 20, "ml": 25, "behavior": 15},
            recommended_action="MONITOR" if r_score < 60 else "CONTAIN_AND_ALERT"
        )
        db.add(ra)

        # Add Anomaly record
        anom = Anomaly(
            organization_id=org.id,
            event_id=ev.id,
            model_version="v1.0.0-isolation-forest",
            anomaly_score=r_score,
            is_anomaly=(r_score >= 60),
            reasons=["Seeded security telemetry record"]
        )
        db.add(anom)

        # If Critical, create an incident
        if r_level == "critical":
            inc = Incident(
                organization_id=org.id,
                title=f"Critical Security Alert: Automated detection for actor {actor}",
                severity="critical",
                status="Investigating",
                risk_score=r_score,
                event_id=ev.id,
                timeline=[
                    {
                        "timestamp": now.isoformat(),
                        "state": "Detected",
                        "actor": "PRIVASEC_RESPONSE_ENGINE",
                        "message": "Automated incident generated due to brute-force cluster detection."
                    }
                ]
            )
            db.add(inc)

    await db.commit()

    # 7. Initial Cryptographic Hash Chain Audit Logs
    await record_audit_event(
        db=db,
        organization_id=org.id,
        actor_id=created_users["admin@privasec.io"].id,
        action="PLATFORM_INITIALIZATION",
        metadata={"platform": "PRIVASEC v1.0.0", "seed": "complete"}
    )
    await record_audit_event(
        db=db,
        organization_id=org.id,
        actor_id=created_users["privacy@privasec.io"].id,
        action="PRIVACY_POLICY_ESTABLISHED",
        metadata={"policy_count": len(policies)}
    )

    logger.info("PRIVASEC seed completed successfully.")
