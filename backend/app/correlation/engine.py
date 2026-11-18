from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.models import SecurityEvent, Alert, Incident, IncidentEvent, DetectionRule


MITRE_TACTIC_MAP = {
    "T1110.001": {"tactic": "Credential Access", "name": "Brute Force: Password Guessing"},
    "T1046": {"tactic": "Reconnaissance", "name": "Network Service Discovery"},
    "T1071.004": {"tactic": "Command and Control", "name": "Application Layer Protocol: DNS"},
    "T1048": {"tactic": "Exfiltration", "name": "Exfiltration Over Alternative Protocol"},
    "T1499": {"tactic": "Impact", "name": "Endpoint Denial of Service"},
    "T1078": {"tactic": "Initial Access", "name": "Valid Accounts"},
    "T1571": {"tactic": "Command and Control", "name": "Non-Standard Port"},
    "T1059": {"tactic": "Execution", "name": "Command and Scripting Interpreter"}
}


def calculate_risk_score(
    ml_score: float,
    rule_score: float,
    correlation_score: float,
    threat_intel_score: float
) -> Tuple[float, str, Dict[str, Any]]:
    """
    Calculates composite risk score (0-100) and severity classification
    """
    # Clamp all inputs to 0-100
    ml_norm = max(0.0, min(100.0, ml_score))
    rule_norm = max(0.0, min(100.0, rule_score))
    corr_norm = max(0.0, min(100.0, correlation_score))
    intel_norm = max(0.0, min(100.0, threat_intel_score))

    w_ml = settings.RISK_WEIGHT_ML
    w_rule = settings.RISK_WEIGHT_RULE
    w_corr = settings.RISK_WEIGHT_CORRELATION
    w_intel = settings.RISK_WEIGHT_THREAT_INTEL

    composite = (w_ml * ml_norm) + (w_rule * rule_norm) + (w_corr * corr_norm) + (w_intel * intel_norm)
    final_score = round(max(0.0, min(100.0, composite)), 2)

    if final_score >= 70.0:
        severity = "CRITICAL"
    elif final_score >= 50.0:
        severity = "HIGH"
    elif final_score >= 30.0:
        severity = "MEDIUM"
    else:
        severity = "LOW"

    breakdown = {
        "final_score": final_score,
        "severity": severity,
        "components": {
            "ml_score": round(ml_norm, 2),
            "ml_weight": w_ml,
            "rule_score": round(rule_norm, 2),
            "rule_weight": w_rule,
            "correlation_score": round(corr_norm, 2),
            "correlation_weight": w_corr,
            "threat_intel_score": round(intel_norm, 2),
            "threat_intel_weight": w_intel
        },
        "formula": f"({w_ml}×ML) + ({w_rule}×Rule) + ({w_corr}×Correlation) + ({w_intel}×ThreatIntel)"
    }

    return final_score, severity, breakdown


class EventCorrelationEngine:
    def __init__(self, correlation_window_seconds: int = 600):
        self.correlation_window_seconds = correlation_window_seconds

    def correlate_event(self, event: SecurityEvent, db: Session) -> Tuple[float, Optional[Incident], List[str]]:
        """
        Evaluates temporal and entity relationships to discover attack chains
        Returns (correlation_score_0_to_100, correlated_incident, detected_tactics)
        """
        now = event.timestamp or datetime.now(timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)
        window_start = (now - timedelta(seconds=self.correlation_window_seconds)).replace(tzinfo=None)

        # Find recent events matching entity: host_id or source_ip or username
        query = db.query(SecurityEvent).filter(
            SecurityEvent.id != event.id,
            SecurityEvent.timestamp >= window_start
        )

        filters = []
        if event.host_id:
            filters.append(SecurityEvent.host_id == event.host_id)
        if event.source_ip:
            filters.append(SecurityEvent.source_ip == event.source_ip)
        if event.username:
            filters.append(SecurityEvent.username == event.username)

        if not filters:
            return 0.0, None, []

        from sqlalchemy import or_
        related_events = query.filter(or_(*filters)).all()
        if not related_events:
            return 0.0, None, []

        event_types = set([e.event_type for e in related_events] + [event.event_type])
        tactics = set()

        # Check multi-stage chain: e.g. auth_failure + auth_success + process_spawn
        has_auth_fail = "auth_failure" in event_types
        has_auth_succ = "auth_success" in event_types
        has_proc_spawn = "process_spawn" in event_types
        has_network_conn = any("conn" in et for et in event_types) or "zeek_conn" in event_types
        has_recon = "port_scan" in event_types or "zeek_conn" in event_types

        score = min(len(related_events) * 8.0, 40.0)

        if has_auth_fail and has_auth_succ:
            score += 25.0
            tactics.add("Initial Access")

        if (has_auth_succ or has_auth_fail) and has_proc_spawn:
            score += 25.0
            tactics.add("Execution")

        if has_proc_spawn and has_network_conn:
            score += 25.0
            tactics.add("Command and Control")

        if has_recon:
            score += 15.0
            tactics.add("Reconnaissance")

        final_corr_score = min(100.0, score)

        # Check if an active open incident exists for this host/source_ip
        existing_incident = db.query(Incident).filter(
            Incident.status.in_(["NEW", "INVESTIGATING"]),
            Incident.created_at >= window_start
        ).order_by(Incident.id.desc()).first()

        incident = None
        if final_corr_score >= 50.0:
            if existing_incident:
                incident = existing_incident
                # Link this event to incident
                link_exists = db.query(IncidentEvent).filter(
                    IncidentEvent.incident_id == incident.id,
                    IncidentEvent.event_id == event.id
                ).first()
                if not link_exists:
                    db.add(IncidentEvent(incident_id=incident.id, event_id=event.id))
                    incident.risk_score = max(incident.risk_score, final_corr_score)
                    current_tactics = set(incident.mitre_tactics or [])
                    current_tactics.update(tactics)
                    incident.mitre_tactics = list(current_tactics)
                    db.commit()
            else:
                # Create correlated incident
                incident_title = f"Multi-Stage Security Incident on {event.host_id or event.source_ip or 'Network'}"
                incident_desc = f"Correlated {len(related_events) + 1} suspicious events within {self.correlation_window_seconds}s. Involves {', '.join(event_types)}."
                incident = Incident(
                    title=incident_title,
                    description=incident_desc,
                    severity="HIGH" if final_corr_score < 75.0 else "CRITICAL",
                    status="NEW",
                    risk_score=final_corr_score,
                    mitre_tactics=list(tactics)
                )
                db.add(incident)
                db.commit()
                db.refresh(incident)

                # Link events
                db.add(IncidentEvent(incident_id=incident.id, event_id=event.id))
                for re in related_events[:5]:
                    db.add(IncidentEvent(incident_id=incident.id, event_id=re.id))
                db.commit()

        return round(final_corr_score, 2), incident, list(tactics)


correlation_engine = EventCorrelationEngine()
