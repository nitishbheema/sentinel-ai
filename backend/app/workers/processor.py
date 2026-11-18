from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.models import (
    SecurityEvent,
    Prediction,
    Alert,
    Incident,
    IncidentEvent,
    ResponseAction
)
from app.detection.engine import rule_engine
from app.detection.ml_engine import ml_engine
from app.threat_intelligence.matcher import check_threat_intelligence
from app.correlation.engine import correlation_engine, calculate_risk_score, MITRE_TACTIC_MAP


def process_normalized_event(event_data: Dict[str, Any], db: Session) -> Dict[str, Any]:
    """
    Core pipeline orchestrator for an ingested event:
    1. Persist Event
    2. Run ML Models (Random Forest + Isolation Forest)
    3. Run Rule Engine
    4. Run Threat Intelligence Matcher
    5. Run Correlation Engine
    6. Calculate Composite Risk Score
    7. Generate Alerts and link Incidents
    8. Suggest Defensive Response Actions
    """
    # 1. Deduplication check
    checksum = event_data.get("hash_checksum")
    if checksum:
        existing = db.query(SecurityEvent).filter(SecurityEvent.hash_checksum == checksum).first()
        if existing:
            return {
                "status": "duplicate_skipped",
                "event_id": existing.id,
                "event_uuid": existing.event_uuid,
                "detected_alerts": 0
            }

    # Persist security event
    event = SecurityEvent(
        event_source=event_data["event_source"],
        event_type=event_data["event_type"],
        timestamp=event_data.get("timestamp"),
        source_ip=event_data.get("source_ip"),
        source_port=event_data.get("source_port"),
        destination_ip=event_data.get("destination_ip"),
        destination_port=event_data.get("destination_port"),
        protocol=event_data.get("protocol"),
        host_id=event_data.get("host_id"),
        username=event_data.get("username"),
        process_name=event_data.get("process_name"),
        process_pid=event_data.get("process_pid"),
        raw_data=event_data.get("raw_data"),
        normalized_data=event_data.get("normalized_data"),
        hash_checksum=checksum
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    # 2. Machine Learning Inference
    ml_result = ml_engine.predict_event(event_data)
    ml_pred = Prediction(
        event_id=event.id,
        model_name="RandomForest+IsolationForest",
        model_version="1.0.0",
        prediction_label=ml_result["classification"],
        confidence=ml_result["confidence"],
        anomaly_score=ml_result["anomaly_score"],
        feature_contributions=ml_result["feature_contributions"]
    )
    db.add(ml_pred)
    db.commit()
    db.refresh(ml_pred)

    # ML Score (0-100)
    ml_score = 0.0
    if ml_result["classification"] != "BENIGN":
        ml_score = max(ml_score, ml_result["confidence"] * 100.0)
    if ml_result["is_anomaly"]:
        ml_score = max(ml_score, ml_result["anomaly_score"] * 100.0)

    # 3. Rule-based Evaluation
    rule_alerts = rule_engine.evaluate_event(event, db)
    rule_score = 0.0
    if rule_alerts:
        severities = [a["severity"] for a in rule_alerts]
        if "CRITICAL" in severities:
            rule_score = 100.0
        elif "HIGH" in severities:
            rule_score = 80.0
        elif "MEDIUM" in severities:
            rule_score = 50.0
        else:
            rule_score = 30.0

    # 4. Threat Intelligence Check
    threat_match = check_threat_intelligence(
        db,
        source_ip=event.source_ip,
        destination_ip=event.destination_ip
    )
    threat_intel_score = threat_match["score"] if threat_match else 0.0

    # 5. Correlation & Incident Discovery
    correlation_score, correlated_incident, tactics = correlation_engine.correlate_event(event, db)

    # 6. Composite Risk Calculation
    final_risk, severity, risk_breakdown = calculate_risk_score(
        ml_score=ml_score,
        rule_score=rule_score,
        correlation_score=correlation_score,
        threat_intel_score=threat_intel_score
    )

    created_alerts = []

    # Generate Alert if Rule matched or ML detected attack or Threat Intel matched
    should_alert = bool(rule_alerts) or (ml_result["classification"] != "BENIGN") or (threat_match is not None) or (final_risk >= 50.0)

    if should_alert:
        title = "Security Alert"
        desc = ""
        mitre_tech = None

        alert_sev = severity
        if rule_alerts:
            first_ra = rule_alerts[0]
            title = first_ra["title"]
            desc = first_ra["description"]
            mitre_tech = first_ra["mitre_technique"]
            rule_sev = first_ra.get("severity", "MEDIUM")
            if rule_sev in ["HIGH", "CRITICAL"]:
                alert_sev = rule_sev
                final_risk = max(final_risk, 75.0 if rule_sev == "CRITICAL" else 60.0)
        elif threat_match:
            title = f"Threat Intel Hit: Known {threat_match['threat_type']}"
            desc = f"Matched indicator {threat_match['value']} from source {threat_match['source']} (confidence: {threat_match['confidence']}%)."
        elif ml_result["classification"] != "BENIGN":
            title = f"ML Anomaly: {ml_result['classification']} Detected"
            desc = f"ML model flagged flow with {ml_result['confidence']*100:.1f}% confidence and anomaly score {ml_result['anomaly_score']:.2f}."
            mitre_tech = "T1046" if "PortScan" in ml_result["classification"] else "T1499"

        evidence = {
            "ml_prediction": {
                "classification": ml_result["classification"],
                "confidence": ml_result["confidence"],
                "anomaly_score": ml_result["anomaly_score"],
                "is_anomaly": ml_result["is_anomaly"],
                "top_features": ml_result["feature_contributions"]
            },
            "rule_alerts": rule_alerts,
            "threat_intel": threat_match,
            "correlation": {
                "score": correlation_score,
                "incident_id": correlated_incident.id if correlated_incident else None,
                "mitre_tactics": tactics
            }
        }

        alert = Alert(
            title=title,
            description=desc,
            severity=alert_sev,
            status="OPEN",
            source="RULE" if rule_alerts else ("THREAT_INTEL" if threat_match else "ML"),
            rule_id=rule_alerts[0]["rule_id"] if rule_alerts else None,
            event_id=event.id,
            ml_prediction_id=ml_pred.id,
            risk_score=final_risk,
            risk_breakdown=risk_breakdown,
            mitre_technique=mitre_tech,
            evidence=evidence
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)
        created_alerts.append(alert)

        # 7. Generate approval-based defensive response recommendation if High or Critical
        if severity in ["HIGH", "CRITICAL"]:
            target_ip = event.source_ip or event.destination_ip
            if target_ip and not target_ip.startswith("127."):
                action = ResponseAction(
                    incident_id=correlated_incident.id if correlated_incident else None,
                    alert_id=alert.id,
                    action_type="BLOCK_IP",
                    target=target_ip,
                    status="PENDING_APPROVAL",
                    rollback_available=True
                )
                db.add(action)
                db.commit()

            if event.host_id:
                action_iso = ResponseAction(
                    incident_id=correlated_incident.id if correlated_incident else None,
                    alert_id=alert.id,
                    action_type="ISOLATE_HOST",
                    target=event.host_id,
                    status="PENDING_APPROVAL",
                    rollback_available=True
                )
                db.add(action_iso)
                db.commit()

    return {
        "status": "processed",
        "event_id": event.id,
        "event_uuid": event.event_uuid,
        "detected_alerts": len(created_alerts),
        "risk_score": final_risk,
        "severity": severity
    }
