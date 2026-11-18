import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Boolean, Float, DateTime, Text,
    ForeignKey, Table, Index, JSON
)
from sqlalchemy.orm import relationship
from app.database.session import Base


def utc_now():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), default="ANALYST", nullable=False)  # ADMIN, ANALYST, VIEWER
    is_active = Column(Boolean, default=True, nullable=False)
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    assigned_incidents = relationship("Incident", back_populates="assigned_to")
    notes = relationship("IncidentNote", back_populates="author")
    audit_logs = relationship("AuditLog", back_populates="user")


class Endpoint(Base):
    __tablename__ = "endpoints"

    id = Column(Integer, primary_key=True, index=True)
    hostname = Column(String(255), unique=True, index=True, nullable=False)
    ip_address = Column(String(100), index=True, nullable=False)
    os_type = Column(String(50), default="linux", nullable=False)
    os_version = Column(String(100), nullable=True)
    status = Column(String(50), default="ACTIVE", nullable=False)  # ACTIVE, OFFLINE, ISOLATED
    agent_version = Column(String(50), default="1.0.0", nullable=False)
    last_seen = Column(DateTime, default=utc_now, nullable=False)
    isolation_status = Column(Boolean, default=False, nullable=False)
    meta_info = Column(JSON, default=dict, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    agents = relationship("Agent", back_populates="endpoint")


class Agent(Base):
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, index=True)
    endpoint_id = Column(Integer, ForeignKey("endpoints.id", ondelete="CASCADE"), nullable=False)
    agent_type = Column(String(50), default="ENDPOINT", nullable=False)  # ENDPOINT, ZEEK, SURICATA
    status = Column(String(50), default="ONLINE", nullable=False)
    version = Column(String(50), default="1.0.0", nullable=False)
    api_key_hash = Column(String(255), nullable=True)
    last_heartbeat = Column(DateTime, default=utc_now, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    endpoint = relationship("Endpoint", back_populates="agents")


class SecurityEvent(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    event_uuid = Column(String(64), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    event_source = Column(String(50), index=True, nullable=False)  # zeek, suricata, endpoint, auth, network
    event_type = Column(String(100), index=True, nullable=False)
    timestamp = Column(DateTime, default=utc_now, index=True, nullable=False)
    source_ip = Column(String(100), index=True, nullable=True)
    source_port = Column(Integer, nullable=True)
    destination_ip = Column(String(100), index=True, nullable=True)
    destination_port = Column(Integer, nullable=True)
    protocol = Column(String(20), nullable=True)
    host_id = Column(String(100), index=True, nullable=True)
    username = Column(String(100), index=True, nullable=True)
    process_name = Column(String(255), nullable=True)
    process_pid = Column(Integer, nullable=True)
    raw_data = Column(JSON, nullable=True)
    normalized_data = Column(JSON, nullable=True)
    hash_checksum = Column(String(64), index=True, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    predictions = relationship("Prediction", back_populates="event")
    incident_links = relationship("IncidentEvent", back_populates="event")


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    model_name = Column(String(100), nullable=False)
    model_version = Column(String(50), default="1.0.0", nullable=False)
    prediction_label = Column(String(100), nullable=False)  # BENIGN, MALICIOUS, ANOMALY
    confidence = Column(Float, default=0.0, nullable=False)
    anomaly_score = Column(Float, default=0.0, nullable=False)
    feature_contributions = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    event = relationship("SecurityEvent", back_populates="predictions")


class DetectionRule(Base):
    __tablename__ = "detection_rules"

    id = Column(Integer, primary_key=True, index=True)
    rule_id = Column(String(100), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    severity = Column(String(50), default="MEDIUM", nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    category = Column(String(100), default="Network", nullable=False)
    condition_yaml = Column(Text, nullable=False)
    is_enabled = Column(Boolean, default=True, nullable=False)
    time_window_seconds = Column(Integer, default=60, nullable=False)
    threshold = Column(Integer, default=5, nullable=False)
    mitre_technique_id = Column(String(50), nullable=True)
    version = Column(String(20), default="1.0", nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    alerts = relationship("Alert", back_populates="rule")


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    alert_uuid = Column(String(64), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    severity = Column(String(50), default="MEDIUM", index=True, nullable=False)
    status = Column(String(50), default="OPEN", index=True, nullable=False)  # OPEN, TRIAGED, RESOLVED, SUPPRESSED
    source = Column(String(50), default="RULE", nullable=False)  # RULE, ML, CORRELATION
    rule_id = Column(Integer, ForeignKey("detection_rules.id", ondelete="SET NULL"), nullable=True)
    event_id = Column(Integer, ForeignKey("events.id", ondelete="SET NULL"), nullable=True)
    ml_prediction_id = Column(Integer, ForeignKey("predictions.id", ondelete="SET NULL"), nullable=True)
    risk_score = Column(Float, default=0.0, nullable=False)
    risk_breakdown = Column(JSON, nullable=True)
    mitre_technique = Column(String(100), nullable=True)
    evidence = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=utc_now, index=True, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    rule = relationship("DetectionRule", back_populates="alerts")


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    incident_uuid = Column(String(64), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    severity = Column(String(50), default="MEDIUM", index=True, nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    status = Column(String(50), default="NEW", index=True, nullable=False)  # NEW, INVESTIGATING, CONFIRMED, RESOLVED, FALSE_POSITIVE
    assigned_to_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    risk_score = Column(Float, default=0.0, nullable=False)
    mitre_tactics = Column(JSON, default=list, nullable=True)
    created_at = Column(DateTime, default=utc_now, index=True, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    assigned_to = relationship("User", back_populates="assigned_incidents")
    events = relationship("IncidentEvent", back_populates="incident", cascade="all, delete-orphan")
    notes = relationship("IncidentNote", back_populates="incident", cascade="all, delete-orphan")
    response_actions = relationship("ResponseAction", back_populates="incident")


class IncidentEvent(Base):
    __tablename__ = "incident_events"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False)
    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    added_at = Column(DateTime, default=utc_now, nullable=False)

    incident = relationship("Incident", back_populates="events")
    event = relationship("SecurityEvent", back_populates="incident_links")


class IncidentNote(Base):
    __tablename__ = "incident_notes"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    note = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    incident = relationship("Incident", back_populates="notes")
    author = relationship("User", back_populates="notes")


class ResponseAction(Base):
    __tablename__ = "response_actions"

    id = Column(Integer, primary_key=True, index=True)
    action_uuid = Column(String(64), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    incident_id = Column(Integer, ForeignKey("incidents.id", ondelete="SET NULL"), nullable=True)
    alert_id = Column(Integer, ForeignKey("alerts.id", ondelete="SET NULL"), nullable=True)
    action_type = Column(String(50), nullable=False)  # BLOCK_IP, ISOLATE_HOST, RESTRICT_ACCOUNT, NOTIFY_ANALYST
    target = Column(String(255), nullable=False)
    status = Column(String(50), default="PENDING_APPROVAL", nullable=False)  # PENDING_APPROVAL, APPROVED, REJECTED, EXECUTED, FAILED
    requested_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    execution_result = Column(JSON, nullable=True)
    rollback_available = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    incident = relationship("Incident", back_populates="response_actions")


class ThreatIndicator(Base):
    __tablename__ = "threat_indicators"

    id = Column(Integer, primary_key=True, index=True)
    indicator_type = Column(String(50), index=True, nullable=False)  # IP, DOMAIN, HASH
    value = Column(String(255), unique=True, index=True, nullable=False)
    threat_type = Column(String(100), nullable=False)  # C2, MALWARE, PHISHING, SCANNER
    severity = Column(String(50), default="HIGH", nullable=False)
    confidence = Column(Integer, default=80, nullable=False)  # 0 to 100
    source = Column(String(100), default="SentinelLab", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = Column(String(100), index=True, nullable=False)
    target_type = Column(String(50), nullable=True)
    target_id = Column(String(100), nullable=True)
    details = Column(JSON, nullable=True)
    ip_address = Column(String(50), nullable=True)
    timestamp = Column(DateTime, default=utc_now, index=True, nullable=False)

    user = relationship("User", back_populates="audit_logs")
