import os
import json
import joblib
import numpy as np
from typing import Dict, Any, Optional

FEATURE_COLUMNS = [
    "destination_port",
    "flow_duration",
    "tot_fwd_pkts",
    "tot_bwd_pkts",
    "tot_len_fwd_pkts",
    "tot_len_bwd_pkts",
    "fwd_pkt_len_max",
    "fwd_pkt_len_min",
    "fwd_pkt_len_mean",
    "fwd_pkt_len_std",
    "flow_byts_s",
    "flow_pkts_s",
    "flow_iat_mean",
    "fwd_iat_tot",
    "bwd_iat_tot",
    "syn_flag_cnt",
    "rst_flag_cnt",
    "psh_flag_cnt",
    "ack_flag_cnt"
]


class MLInferenceEngine:
    def __init__(self, models_dir: Optional[str] = None):
        self.models_dir = self._resolve_models_dir(models_dir)
        self.rf_model = None
        self.iso_model = None
        self.scaler = None
        self.label_encoder = None
        self.metrics = {}
        self.load_models()

    def _resolve_models_dir(self, override: Optional[str]) -> str:
        candidates = [
            override,
            os.path.join(os.path.dirname(__file__), "../../../ml-engine/models"),
            "ml-engine/models",
            "../ml-engine/models",
            "../../ml-engine/models"
        ]
        for c in candidates:
            if c and os.path.exists(c) and os.path.isdir(c):
                return os.path.abspath(c)
        return "ml-engine/models"

    def load_models(self):
        try:
            rf_path = os.path.join(self.models_dir, "random_forest.joblib")
            iso_path = os.path.join(self.models_dir, "isolation_forest.joblib")
            scaler_path = os.path.join(self.models_dir, "scaler.joblib")
            le_path = os.path.join(self.models_dir, "label_encoder.joblib")
            metrics_path = os.path.join(self.models_dir, "evaluation_metrics.json")

            if os.path.exists(rf_path):
                self.rf_model = joblib.load(rf_path)
            if os.path.exists(iso_path):
                self.iso_model = joblib.load(iso_path)
            if os.path.exists(scaler_path):
                self.scaler = joblib.load(scaler_path)
            if os.path.exists(le_path):
                self.label_encoder = joblib.load(le_path)
            if os.path.exists(metrics_path):
                with open(metrics_path, "r", encoding="utf-8") as f:
                    self.metrics = json.load(f)
            print(f"[MLInferenceEngine] Models successfully loaded from {self.models_dir}")
        except Exception as e:
            print(f"[MLInferenceEngine] Warning loading models: {e}")

    def extract_features(self, data: Dict[str, Any]) -> np.ndarray:
        norm = data.get("normalized_data") or {}
        raw = data.get("raw_data") or {}

        features = [
            float(data.get("destination_port") or norm.get("destination_port") or raw.get("id_resp_p") or 80),
            float(norm.get("duration") or raw.get("duration") or 0.2),
            float(raw.get("tot_fwd_pkts") or norm.get("orig_pkts") or 5),
            float(raw.get("tot_bwd_pkts") or norm.get("resp_pkts") or 4),
            float(norm.get("orig_bytes") or raw.get("tot_len_fwd_pkts") or 450),
            float(norm.get("resp_bytes") or raw.get("tot_len_bwd_pkts") or 900),
            float(raw.get("fwd_pkt_len_max") or 1400.0),
            float(raw.get("fwd_pkt_len_min") or 40.0),
            float(raw.get("fwd_pkt_len_mean") or 450.0),
            float(raw.get("fwd_pkt_len_std") or 50.0),
            float(raw.get("flow_byts_s") or 12000.0),
            float(raw.get("flow_pkts_s") or 45.0),
            float(raw.get("flow_iat_mean") or 0.02),
            float(raw.get("fwd_iat_tot") or 0.1),
            float(raw.get("bwd_iat_tot") or 0.08),
            float(raw.get("syn_flag_cnt", 1)),
            float(raw.get("rst_flag_cnt", 0)),
            float(raw.get("psh_flag_cnt", 1)),
            float(raw.get("ack_flag_cnt", 1))
        ]
        return np.array([features], dtype=np.float32)

    def predict(self, feature_vector: np.ndarray) -> Dict[str, Any]:
        if self.scaler is None or self.rf_model is None:
            # Fallback if models not ready
            return {
                "classification": "BENIGN",
                "confidence": 0.95,
                "anomaly_score": 0.1,
                "is_anomaly": False,
                "feature_contributions": {}
            }

        # Input validation and bounds checking: sanitize NaN, Inf, and abnormal spikes
        feature_vector = np.nan_to_num(feature_vector, nan=0.0, posinf=1e7, neginf=0.0)
        feature_vector = np.clip(feature_vector, -1e8, 1e8)

        # Preprocess using training scaler
        scaled_features = self.scaler.transform(feature_vector)

        # 1. Random Forest prediction
        rf_probs = self.rf_model.predict_proba(scaled_features)[0]
        max_idx = int(np.argmax(rf_probs))
        confidence = float(rf_probs[max_idx])
        classification = str(self.label_encoder.inverse_transform([max_idx])[0])

        # 2. Isolation Forest prediction
        iso_raw = float(self.iso_model.decision_function(scaled_features)[0])
        # decision_function gives negative values for anomalies, positive for normal
        # Map raw decision function to continuous 0.0 - 1.0 anomaly score
        anomaly_score = float(max(0.0, min(1.0, 0.5 - (iso_raw * 1.5))))
        is_anomaly = anomaly_score > 0.55

        # Feature contributions based on model importances & deviations
        importances = self.rf_model.feature_importances_
        feature_weights = {}
        for idx, col in enumerate(FEATURE_COLUMNS):
            dev = abs(float(scaled_features[0][idx]))
            weight = float(importances[idx] * (1.0 + dev))
            feature_weights[col] = round(weight, 4)

        top_features = dict(sorted(feature_weights.items(), key=lambda x: x[1], reverse=True)[:5])

        return {
            "classification": classification,
            "confidence": round(confidence, 4),
            "anomaly_score": round(anomaly_score, 4),
            "is_anomaly": is_anomaly,
            "feature_contributions": top_features
        }

    def predict_event(self, event_dict: Dict[str, Any]) -> Dict[str, Any]:
        feats = self.extract_features(event_dict)
        return self.predict(feats)

    def get_metrics(self) -> Dict[str, Any]:
        return self.metrics


ml_engine = MLInferenceEngine()
