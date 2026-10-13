from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.event_bus import emit_security_event
from app.modules.privacy.pii_detector import pii_detector
from app.modules.privacy.data_masker import apply_masking_to_text
from app.modules.privacy.pseudonymizer import create_pseudonym_mapping


SCENARIOS_CATALOG = [
    {
        "id": "brute_force",
        "name": "Brute-Force Authentication Attack",
        "category": "Identity & Access",
        "severity": "critical",
        "description": "Simulates 12 rapid failed authentication attempts from a novel IP address, demonstrating rate limiting, behavioral penalty, critical risk scoring, and automated session revocation.",
        "expected_outcome": "Rate limit exceeded, composite risk score >= 80, automated incident created, session contained."
    },
    {
        "id": "sqli_probe",
        "name": "SQL Injection Gateway Probe",
        "category": "Web & API Security",
        "severity": "high",
        "description": "Simulates malicious query payloads (' OR '1'='1 --) targeting query endpoints. Demonstrates parameterization safety, application-layer telemetry detection, and threat factor attribution.",
        "expected_outcome": "Safe execution via parameterized ORM, SQL_INJECTION_INDICATOR logged, API security risk factor elevated."
    },
    {
        "id": "api_burst",
        "name": "Suspicious High-Volume API Burst",
        "category": "Web & API Security",
        "severity": "high",
        "description": "Simulates 300 requests/minute scraping burst. Demonstrates sliding-window throttling, Isolation Forest velocity anomaly detection, and analyst alert generation.",
        "expected_outcome": "429 Rate limiting triggered, Isolation Forest flags rate anomaly, High risk score."
    },
    {
        "id": "novel_device",
        "name": "Unrecognized Device & Off-Hours Login",
        "category": "Behavioral Intelligence",
        "severity": "medium",
        "description": "Simulates authentication from an unobserved device hash during off-peak night hours. Demonstrates rolling baseline comparison, device novelty penalty, and adaptive MFA challenge.",
        "expected_outcome": "Behavioral deviation computed, adaptive authentication mandates TOTP step-up."
    },
    {
        "id": "data_exfil",
        "name": "Anomalous Sensitive Data Export",
        "category": "Privacy & Data Protection",
        "severity": "high",
        "description": "Simulates an attempt to download 15 MB of customer records at unusual hours. Demonstrates data sensitivity weighting, privacy policy enforcement, and containment triage.",
        "expected_outcome": "Data sensitivity factor scores 85+, risk elevated, step-up/analyst approval required."
    },
    {
        "id": "pii_document_scan",
        "name": "PII Detection & Privacy Transformation",
        "category": "Privacy Engineering",
        "severity": "medium",
        "description": "Simulates processing an employee document containing Indian PAN cards, Aadhaar IDs, credit card numbers, and email addresses. Demonstrates Presidio recognition, format-preserving masking, and HMAC pseudonymization.",
        "expected_outcome": "All sensitive entities recognized, masked preview generated, HMAC token mapped in vault."
    }
]


class SecuritySimulationService:
    async def run_scenario(
        self,
        db: AsyncSession,
        organization_id: str,
        scenario_id: str,
        actor_pseudonym: str = "sim_actor_9a2f",
        user_id: str = None
    ) -> Dict[str, Any]:
        """Executes selected local security simulation scenario through the real pipeline."""
        if scenario_id == "brute_force":
            result = await emit_security_event(
                db=db,
                organization_id=organization_id,
                actor_pseudonym=actor_pseudonym,
                event_type="AUTH_BRUTE_FORCE_BURST",
                source="simulation",
                severity="critical",
                network={"ip_token": "ip_sim_attacker_8b", "country_code": "RU"},
                device={"device_hash": "dev_unknown_bot_01", "recognized": False},
                metrics={"failed_logins_5m": 12, "requests_per_minute": 85.0, "access_denials_5m": 8},
                sensitivity="medium",
                metadata={"reason": "Simulated credential stuffing cluster", "endpoint_rarity": 0.4},
                user_id=user_id
            )
            return {"scenario": "Brute-Force Authentication Attack", "pipeline_result": result}

        elif scenario_id == "sqli_probe":
            result = await emit_security_event(
                db=db,
                organization_id=organization_id,
                actor_pseudonym=actor_pseudonym,
                event_type="GATEWAY_PROBE_SQLI",
                source="simulation",
                severity="high",
                network={"ip_token": "ip_sim_scanner_1c", "country_code": "US"},
                device={"device_hash": "dev_curl_python_req", "recognized": False},
                metrics={"failed_logins_5m": 0, "requests_per_minute": 30.0, "access_denials_5m": 2},
                sensitivity="high",
                metadata={
                    "detected_threats": ["SQL_INJECTION_INDICATOR", "OR_1_EQUALS_1"],
                    "endpoint_rarity": 0.85,
                    "target_endpoint": "/api/users?query=' UNION SELECT username, password_hash FROM users --"
                },
                user_id=user_id
            )
            return {"scenario": "SQL Injection Gateway Probe", "pipeline_result": result}

        elif scenario_id == "api_burst":
            result = await emit_security_event(
                db=db,
                organization_id=organization_id,
                actor_pseudonym=actor_pseudonym,
                event_type="API_SCRAPING_BURST",
                source="simulation",
                severity="high",
                network={"ip_token": "ip_sim_crawler_55", "country_code": "CN"},
                device={"device_hash": "dev_headless_chrome", "recognized": False},
                metrics={"failed_logins_5m": 0, "requests_per_minute": 280.0, "access_denials_5m": 14},
                sensitivity="medium",
                metadata={"endpoint_rarity": 0.7, "detected_threats": ["RATE_LIMIT_EXCEEDED"]},
                user_id=user_id
            )
            return {"scenario": "Suspicious High-Volume API Burst", "pipeline_result": result}

        elif scenario_id == "novel_device":
            result = await emit_security_event(
                db=db,
                organization_id=organization_id,
                actor_pseudonym=actor_pseudonym,
                event_type="AUTH_NEW_DEVICE_LOGIN",
                source="simulation",
                severity="medium",
                network={"ip_token": "ip_sim_mobile_4g", "country_code": "SG"},
                device={"device_hash": "dev_ios_safari_new_99", "recognized": False},
                metrics={"failed_logins_5m": 0, "requests_per_minute": 12.0, "access_denials_5m": 0},
                sensitivity="medium",
                metadata={"endpoint_rarity": 0.2, "hour_utc": 2},
                user_id=user_id
            )
            return {"scenario": "Unrecognized Device & Off-Hours Login", "pipeline_result": result}

        elif scenario_id == "data_exfil":
            result = await emit_security_event(
                db=db,
                organization_id=organization_id,
                actor_pseudonym=actor_pseudonym,
                event_type="DATA_BULK_EXPORT_ANOMALOUS",
                source="simulation",
                severity="high",
                network={"ip_token": "ip_sim_internal_vpn", "country_code": "IN"},
                device={"device_hash": "dev_standard_workstation", "recognized": True},
                metrics={"failed_logins_5m": 0, "requests_per_minute": 45.0, "access_denials_5m": 0},
                sensitivity="critical",
                metadata={"export_volume_kb": 15000.0, "endpoint_rarity": 0.95, "record_count": 50000},
                user_id=user_id
            )
            return {"scenario": "Anomalous Sensitive Data Export", "pipeline_result": result}

        elif scenario_id == "pii_document_scan":
            sample_text = (
                "Customer Onboarding Record:\n"
                "Name: Rahul Sharma, Email: rahul.sharma@example.com, Phone: +91 9876543210\n"
                "Income Tax PAN: ABCDE1234F, Aadhaar Number: 5432 9876 1234\n"
                "Corporate Credit Card: 4532 0150 9821 1234, API Key: sec_key_9a8b7c6d5e4f3a2b1c0d9e8f\n"
                "Location: Cyber City, Gurugram, India, IP Address: 192.168.1.105"
            )
            findings = pii_detector.scan_text(sample_text)
            masked_text = apply_masking_to_text(sample_text, findings, default_strategy="PARTIAL")
            
            # Pseudonymize email
            pseudonym = await create_pseudonym_mapping(
                db=db,
                organization_id=organization_id,
                original_identifier="rahul.sharma@example.com",
                purpose="onboarding_demo"
            )

            # Emit security event
            event_result = await emit_security_event(
                db=db,
                organization_id=organization_id,
                actor_pseudonym=actor_pseudonym,
                event_type="PRIVACY_PII_SCAN_EXECUTED",
                source="simulation",
                severity="low",
                network={"ip_token": "ip_sim_internal", "country_code": "IN"},
                device={"device_hash": "dev_workstation", "recognized": True},
                metrics={"requests_per_minute": 15.0},
                sensitivity="high",
                metadata={"pii_entities_detected": len(findings), "export_volume_kb": 2.5},
                user_id=user_id
            )

            return {
                "scenario": "PII Detection & Privacy Transformation",
                "sample_original_text": sample_text,
                "detected_pii_entities": findings,
                "masked_preview": masked_text,
                "pseudonymized_token": pseudonym,
                "pipeline_result": event_result
            }

        else:
            raise ValueError(f"Unknown scenario ID: {scenario_id}")


simulation_service = SecuritySimulationService()
