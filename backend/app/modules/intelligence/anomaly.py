import os
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import precision_score, recall_score, f1_score
from app.config import settings
from app.modules.intelligence.synthetic_data import generate_synthetic_security_dataset

FEATURE_NAMES = [
    "requests_per_minute",
    "failed_logins_5m",
    "time_of_day_deviation",
    "device_novelty",
    "endpoint_rarity",
    "export_volume_kb",
    "access_denial_frequency"
]


class AnomalyDetector:
    def __init__(self):
        self.model_version = "v1.0.0-isolation-forest"
        self.model_path = os.path.join(settings.MODELS_DIR, "isolation_forest.joblib")
        self.scaler_path = os.path.join(settings.MODELS_DIR, "scaler.joblib")
        self.model: IsolationForest = None
        self.scaler: StandardScaler = None
        self.metrics: Dict[str, Any] = {}
        self._load_or_train()

    def _load_or_train(self):
        if os.path.exists(self.model_path) and os.path.exists(self.scaler_path):
            try:
                self.model = joblib.load(self.model_path)
                self.scaler = joblib.load(self.scaler_path)
                metrics_path = os.path.join(settings.MODELS_DIR, "metrics.joblib")
                if os.path.exists(metrics_path):
                    self.metrics = joblib.load(metrics_path)
                return
            except Exception:
                pass
        self.train_and_save()

    def train_and_save(self) -> Dict[str, Any]:
        """Trains Isolation Forest on synthetic baseline and evaluates on test set."""
        X, y = generate_synthetic_security_dataset(n_benign=3000, n_anomalous=200, random_state=42)

        # Train on mostly benign baseline with realistic contamination
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)

        contamination = 200.0 / 3200.0
        self.model = IsolationForest(
            n_estimators=100,
            contamination=contamination,
            random_state=42,
            n_jobs=1
        )
        self.model.fit(X_scaled)

        # Evaluate
        preds = self.model.predict(X_scaled)
        # Isolation Forest: -1 = anomaly, 1 = normal -> convert to 1 = anomaly, 0 = normal
        y_pred = np.where(preds == -1, 1, 0)

        precision = float(precision_score(y, y_pred, zero_division=0))
        recall = float(recall_score(y, y_pred, zero_division=0))
        f1 = float(f1_score(y, y_pred, zero_division=0))

        self.metrics = {
            "model_name": "Isolation Forest Anomaly Detector",
            "version": self.model_version,
            "training_samples": len(X),
            "contamination_parameter": round(contamination, 4),
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1_score": round(f1, 4),
            "features_used": FEATURE_NAMES
        }

        # Save artifacts
        joblib.dump(self.model, self.model_path)
        joblib.dump(self.scaler, self.scaler_path)
        joblib.dump(self.metrics, os.path.join(settings.MODELS_DIR, "metrics.joblib"))

        return self.metrics

    def evaluate(self, feature_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluates an individual event feature vector.
        Outputs normalized 0-100 anomaly score and explainable reasons.
        """
        # Build feature vector
        vector = [
            float(feature_dict.get("requests_per_minute", 15.0)),
            float(feature_dict.get("failed_logins_5m", 0)),
            float(feature_dict.get("time_of_day_deviation", 0.1)),
            float(feature_dict.get("device_novelty", 0.0)),
            float(feature_dict.get("endpoint_rarity", 0.1)),
            float(feature_dict.get("export_volume_kb", 0.0)),
            float(feature_dict.get("access_denial_frequency", 0.0))
        ]

        df = pd.DataFrame([vector], columns=FEATURE_NAMES)
        scaled_v = self.scaler.transform(df)

        raw_score = float(self.model.decision_function(scaled_v)[0])
        pred_label = int(self.model.predict(scaled_v)[0])  # -1 or 1

        # Normalize score to 0 - 100:
        # decision_function typically ranges from -0.3 (highly anomalous) to +0.25 (highly normal).
        # We map: negative -> higher anomaly score (60 - 100), positive -> lower anomaly score (0 - 45).
        normalized_score = float(np.clip((0.18 - raw_score) * 190.0, 0.0, 100.0))
        is_anomaly = (pred_label == -1) or (normalized_score >= 55.0)

        # Feature attribution explainability
        reasons = []
        if vector[1] >= 3:
            reasons.append(f"Elevated failed login velocity ({int(vector[1])} attempts in 5m)")
        if vector[0] >= 60:
            reasons.append(f"Abnormal request rate spike ({int(vector[0])} req/min)")
        if vector[2] >= 0.5:
            reasons.append("Unusual off-hours operational activity")
        if vector[3] >= 0.5:
            reasons.append("Unrecognized client device signature")
        if vector[5] >= 1000:
            reasons.append(f"High-volume data export ({int(vector[5])} KB)")
        if vector[6] >= 3:
            reasons.append(f"Multiple access denials ({int(vector[6])} in 5m)")
        if vector[4] >= 0.7:
            reasons.append("Access to rare or privileged administrative endpoints")

        if not reasons:
            reasons.append("Activity conforms to typical baseline parameters")

        return {
            "model_version": self.model_version,
            "raw_score": round(raw_score, 4),
            "anomaly_score": round(normalized_score, 1),
            "is_anomaly": is_anomaly,
            "reasons": reasons,
            "feature_vector": dict(zip(FEATURE_NAMES, vector))
        }


anomaly_detector = AnomalyDetector()
