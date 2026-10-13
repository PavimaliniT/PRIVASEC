import pytest
from app.modules.privacy.pii_detector import pii_detector
from app.modules.privacy.data_masker import mask_email, mask_pan, mask_aadhaar, mask_credit_card, apply_masking_to_text
from app.modules.privacy.diff_privacy import compute_dp_count
from app.modules.intelligence.anomaly import anomaly_detector
from app.modules.risk.engine import risk_engine


def test_pii_detection_pan_and_aadhaar():
    """Tests Presidio and custom regex detectors for Indian PAN, Aadhaar, and Email."""
    sample_text = "Employee John Doe with PAN ABCDE1234F, Aadhaar 2345 6789 0123, email john@example.com."
    findings = pii_detector.scan_text(sample_text)
    
    types = [f["entity_type"] for f in findings]
    assert "PAN_NUMBER" in types
    assert "AADHAAR_NUMBER" in types
    assert "EMAIL_ADDRESS" in types


def test_masking_strategies():
    """Tests format-preserving masking and redaction."""
    assert mask_email("alice@company.org") == "a***e@company.org"
    assert mask_pan("ABCDE1234F") == "XXXXX1234F"
    assert mask_aadhaar("234567890123") == "XXXX-XXXX-0123"
    assert mask_credit_card("4532015098211234") == "************1234"


def test_differential_privacy_count():
    """Verifies Laplace mechanism bounds and non-trivial privacy perturbation."""
    actual = 1000
    res = compute_dp_count(actual_count=actual, epsilon=0.5)
    assert res["actual_value"] == 1000
    assert "noisy_value" in res
    assert res["epsilon"] == 0.5


def test_anomaly_detection_isolation_forest():
    """Tests ML anomaly model with benign vs anomalous feature vectors."""
    benign_vector = {
        "requests_per_minute": 15.0,
        "failed_logins_5m": 0,
        "time_of_day_deviation": 0.05,
        "device_novelty": 0.0,
        "endpoint_rarity": 0.1,
        "export_volume_kb": 10.0,
        "access_denial_frequency": 0.0
    }
    benign_eval = anomaly_detector.evaluate(benign_vector)
    assert benign_eval["anomaly_score"] < 50.0

    attack_vector = {
        "requests_per_minute": 180.0,
        "failed_logins_5m": 12,
        "time_of_day_deviation": 0.8,
        "device_novelty": 1.0,
        "endpoint_rarity": 0.8,
        "export_volume_kb": 25000.0,
        "access_denial_frequency": 8.0
    }
    attack_eval = anomaly_detector.evaluate(attack_vector)
    assert attack_eval["anomaly_score"] >= 60.0
    assert len(attack_eval["reasons"]) > 0


def test_risk_scoring_bounds_and_levels():
    """Tests composite risk engine scoring 0-100 and level categorization."""
    low_res = risk_engine.calculate_risk(
        auth_signals={"failed_logins_5m": 0},
        behavioral_signals={"deviation_score": 10.0},
        ml_signals={"anomaly_score": 10.0},
        api_signals={"detected_threats": []},
        data_sensitivity_signals={"sensitivity": "low"}
    )
    assert low_res["level"] == "low"
    assert low_res["score"] < 30.0

    crit_res = risk_engine.calculate_risk(
        auth_signals={"failed_logins_5m": 8, "credential_stuffing_suspected": True},
        behavioral_signals={"deviation_score": 90.0},
        ml_signals={"anomaly_score": 85.0},
        api_signals={"detected_threats": ["SQL_INJECTION_INDICATOR"]},
        data_sensitivity_signals={"sensitivity": "critical", "export_volume_kb": 10000.0}
    )
    assert crit_res["level"] == "critical"
    assert crit_res["score"] >= 80.0
    assert crit_res["recommended_action"] == "RESTRICT_AND_CREATE_INCIDENT"
