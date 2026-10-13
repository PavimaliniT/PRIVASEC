from typing import Dict, Any, List
from app.config import settings


class RiskScoringEngine:
    def __init__(self):
        self.w_auth = settings.RISK_WEIGHT_AUTH                    # 0.25
        self.w_behavior = settings.RISK_WEIGHT_BEHAVIOR            # 0.20
        self.w_ml = settings.RISK_WEIGHT_ML_ANOMALY                # 0.20
        self.w_api = settings.RISK_WEIGHT_API_SECURITY             # 0.20
        self.w_sensitivity = settings.RISK_WEIGHT_DATA_SENSITIVITY # 0.15

    def calculate_risk(
        self,
        auth_signals: Dict[str, Any],
        behavioral_signals: Dict[str, Any],
        ml_signals: Dict[str, Any],
        api_signals: Dict[str, Any],
        data_sensitivity_signals: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Computes explainable composite security risk score on a 0-100 scale.
        """
        # 1. Normalize Authentication Factor (0 - 100)
        failed_logins = auth_signals.get("failed_logins_5m", 0)
        is_cred_stuffing = auth_signals.get("credential_stuffing_suspected", False)
        auth_score = min(100.0, (failed_logins * 18.0) + (60.0 if is_cred_stuffing else 0.0))

        # 2. Normalize Behavioral Factor (0 - 100)
        behavior_score = float(behavioral_signals.get("deviation_score", 10.0))

        # 3. Normalize ML Anomaly Factor (0 - 100)
        ml_score = float(ml_signals.get("anomaly_score", 10.0))

        # 4. Normalize API Security Gateway Factor (0 - 100)
        threat_count = len(api_signals.get("detected_threats", []))
        rate_limited = api_signals.get("rate_limited", False)
        api_score = min(100.0, (threat_count * 45.0) + (40.0 if rate_limited else 0.0))

        # 5. Normalize Data Sensitivity Factor (0 - 100)
        sensitivity_level = data_sensitivity_signals.get("sensitivity", "low").lower()
        export_kb = float(data_sensitivity_signals.get("export_volume_kb", 0.0))
        
        base_sens = {"low": 10.0, "medium": 35.0, "high": 70.0, "critical": 95.0}.get(sensitivity_level, 10.0)
        export_bonus = min(30.0, (export_kb / 1000.0) * 10.0)
        sensitivity_score = min(100.0, base_sens + export_bonus)

        # Composite Weighted Score
        composite_score = (
            (auth_score * self.w_auth) +
            (behavior_score * self.w_behavior) +
            (ml_score * self.w_ml) +
            (api_score * self.w_api) +
            (sensitivity_score * self.w_sensitivity)
        )
        final_score = round(min(100.0, max(0.0, composite_score)), 1)

        # Classify Level
        if final_score < 30.0:
            level = "low"
            recommended_action = "ALLOW"
        elif final_score < 60.0:
            level = "medium"
            recommended_action = "MONITOR_OR_STEP_UP"
        elif final_score < 80.0:
            level = "high"
            recommended_action = "REQUIRE_MFA_STEP_UP"
        else:
            level = "critical"
            recommended_action = "RESTRICT_AND_CREATE_INCIDENT"

        # Explainability synthesis
        factors_explanation = []
        if auth_score >= 40:
            factors_explanation.append(f"Authentication risk signal elevated ({auth_score:.0f}/100)")
        if behavior_score >= 40:
            factors_explanation.extend(behavioral_signals.get("deviation_reasons", ["Behavioral baseline deviation detected"]))
        if ml_score >= 50:
            factors_explanation.extend(ml_signals.get("reasons", ["ML Isolation Forest flagged anomalous vector"]))
        if api_score >= 40:
            threats = ", ".join(api_signals.get("detected_threats", ["High request burst"]))
            factors_explanation.append(f"Gateway detected indicators: {threats}")
        if sensitivity_score >= 60:
            factors_explanation.append(f"Target resource involves {sensitivity_level.upper()} sensitivity data")

        if not factors_explanation:
            factors_explanation.append("Signals within nominal operational envelope")

        return {
            "score": final_score,
            "level": level,
            "recommended_action": recommended_action,
            "contributing_factors": {
                "authentication": {
                    "score": round(auth_score, 1),
                    "weight": self.w_auth,
                    "weighted_contribution": round(auth_score * self.w_auth, 1)
                },
                "behavioral_deviation": {
                    "score": round(behavior_score, 1),
                    "weight": self.w_behavior,
                    "weighted_contribution": round(behavior_score * self.w_behavior, 1)
                },
                "ml_anomaly": {
                    "score": round(ml_score, 1),
                    "weight": self.w_ml,
                    "weighted_contribution": round(ml_score * self.w_ml, 1)
                },
                "api_security": {
                    "score": round(api_score, 1),
                    "weight": self.w_api,
                    "weighted_contribution": round(api_score * self.w_api, 1)
                },
                "data_sensitivity": {
                    "score": round(sensitivity_score, 1),
                    "weight": self.w_sensitivity,
                    "weighted_contribution": round(sensitivity_score * self.w_sensitivity, 1)
                }
            },
            "reasons": factors_explanation
        }


risk_engine = RiskScoringEngine()
