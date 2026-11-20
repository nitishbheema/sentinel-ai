from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field


# ==================== User & Auth Schemas ====================

class UserBase(BaseModel):
    username: str
    email: str
    role: str = "ANALYST"
    is_active: bool = True


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None


class UserOut(UserBase):
    id: int
    failed_login_attempts: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserOut


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class AdminSetupRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str
    password: str = Field(..., min_length=12)


class SetupStatusResponse(BaseModel):
    setup_required: bool
    user_count: int
    message: str


# ==================== Endpoint & Agent Schemas ====================

class EndpointBase(BaseModel):
    hostname: str
    ip_address: str
    os_type: str = "linux"
    os_version: Optional[str] = None
    status: str = "ACTIVE"
    agent_version: str = "1.0.0"
    isolation_status: bool = False
    meta_info: Optional[Dict[str, Any]] = None


class EndpointCreate(EndpointBase):
    pass


class EndpointOut(EndpointBase):
    id: int
    last_seen: datetime
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== Event Schemas ====================

class SecurityEventBase(BaseModel):
    event_source: str
    event_type: str
    timestamp: Optional[datetime] = None
    source_ip: Optional[str] = None
    source_port: Optional[int] = None
    destination_ip: Optional[str] = None
    destination_port: Optional[int] = None
    protocol: Optional[str] = None
    host_id: Optional[str] = None
    username: Optional[str] = None
    process_name: Optional[str] = None
    process_pid: Optional[int] = None
    raw_data: Optional[Dict[str, Any]] = None


class SecurityEventCreate(SecurityEventBase):
    pass


class SecurityEventOut(SecurityEventBase):
    id: int
    event_uuid: str
    normalized_data: Optional[Dict[str, Any]] = None
    hash_checksum: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class IngestionResponse(BaseModel):
    status: str
    event_id: int
    event_uuid: str
    detected_alerts: int = 0
    message: str


# Special Ingestion Inputs
class ZeekConnLog(BaseModel):
    ts: float
    uid: str
    id_orig_h: str
    id_orig_p: int
    id_resp_h: str
    id_resp_p: int
    proto: str
    service: Optional[str] = None
    duration: Optional[float] = 0.0
    orig_bytes: Optional[int] = 0
    resp_bytes: Optional[int] = 0
    conn_state: Optional[str] = None


class SuricataEveAlert(BaseModel):
    timestamp: str
    flow_id: Optional[int] = None
    src_ip: str
    src_port: int
    dest_ip: str
    dest_port: int
    proto: str
    alert: Dict[str, Any]


class EndpointTelemetryEvent(BaseModel):
    timestamp: Optional[str] = None
    hostname: str
    ip_address: str
    event_type: str  # auth_failure, auth_success, process_spawn, network_conn, file_mod
    username: Optional[str] = None
    process_name: Optional[str] = None
    pid: Optional[int] = None
    parent_pid: Optional[int] = None
    details: Optional[Dict[str, Any]] = None


# ==================== ML & Prediction Schemas ====================

class PredictionOut(BaseModel):
    id: int
    event_id: int
    model_name: str
    model_version: str
    prediction_label: str
    confidence: float
    anomaly_score: float
    feature_contributions: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class MLPredictRequest(BaseModel):
    flow_duration: float = 0.0
    tot_fwd_pkts: int = 1
    tot_bwd_pkts: int = 0
    tot_len_fwd_pkts: float = 0.0
    tot_len_bwd_pkts: float = 0.0
    fwd_pkt_len_max: float = 0.0
    fwd_pkt_len_min: float = 0.0
    fwd_pkt_len_mean: float = 0.0
    fwd_pkt_len_std: float = 0.0
    flow_byts_s: float = 0.0
    flow_pkts_s: float = 0.0
    flow_iat_mean: float = 0.0
    fwd_iat_tot: float = 0.0
    bwd_iat_tot: float = 0.0
    syn_flag_cnt: int = 0
    rst_flag_cnt: int = 0
    psh_flag_cnt: int = 0
    ack_flag_cnt: int = 0
    destination_port: int = 80


class MLPredictResponse(BaseModel):
    random_forest_classification: str
    random_forest_confidence: float
    isolation_forest_anomaly_score: float
    is_anomaly: bool
    feature_importance: Dict[str, float]
    shap_explanation: Optional[Dict[str, float]] = None


class MLModelMetricsOut(BaseModel):
    model_name: str
    model_type: str
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    false_positive_rate: float
    confusion_matrix: List[List[int]]
    classes: List[str]
    training_samples: int
    evaluation_dataset: str


# ==================== Detection Rules ====================

class DetectionRuleBase(BaseModel):
    rule_id: str
    name: str
    description: Optional[str] = None
    severity: str = "MEDIUM"
    category: str = "Network"
    condition_yaml: str
    is_enabled: bool = True
    time_window_seconds: int = 60
    threshold: int = 5
    mitre_technique_id: Optional[str] = None
    version: str = "1.0"


class DetectionRuleCreate(DetectionRuleBase):
    pass


class DetectionRuleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    severity: Optional[str] = None
    condition_yaml: Optional[str] = None
    is_enabled: Optional[bool] = None
    time_window_seconds: Optional[int] = None
    threshold: Optional[int] = None
    mitre_technique_id: Optional[str] = None


class DetectionRuleOut(DetectionRuleBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== Alert Schemas ====================

class AlertOut(BaseModel):
    id: int
    alert_uuid: str
    title: str
    description: Optional[str] = None
    severity: str
    status: str
    source: str
    rule_id: Optional[int] = None
    event_id: Optional[int] = None
    ml_prediction_id: Optional[int] = None
    risk_score: float
    risk_breakdown: Optional[Dict[str, Any]] = None
    mitre_technique: Optional[str] = None
    evidence: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AlertUpdate(BaseModel):
    status: Optional[str] = None
    severity: Optional[str] = None


# ==================== Incident Schemas ====================

class IncidentCreate(BaseModel):
    title: str
    description: Optional[str] = None
    severity: str = "MEDIUM"
    status: str = "NEW"
    assigned_to_user_id: Optional[int] = None
    risk_score: float = 0.0
    mitre_tactics: Optional[List[str]] = None
    event_ids: Optional[List[int]] = None


class IncidentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    severity: Optional[str] = None
    status: Optional[str] = None
    assigned_to_user_id: Optional[int] = None
    risk_score: Optional[float] = None
    mitre_tactics: Optional[List[str]] = None


class IncidentNoteCreate(BaseModel):
    note: str


class IncidentNoteOut(BaseModel):
    id: int
    incident_id: int
    user_id: Optional[int] = None
    author_username: Optional[str] = None
    note: str
    created_at: datetime

    class Config:
        from_attributes = True


class IncidentOut(BaseModel):
    id: int
    incident_uuid: str
    title: str
    description: Optional[str] = None
    severity: str
    status: str
    assigned_to_user_id: Optional[int] = None
    assigned_to_username: Optional[str] = None
    risk_score: float
    mitre_tactics: Optional[List[str]] = None
    created_at: datetime
    updated_at: datetime
    events_count: int = 0
    notes: List[IncidentNoteOut] = []

    class Config:
        from_attributes = True


# ==================== Response Action Schemas ====================

class ResponseActionCreate(BaseModel):
    incident_id: Optional[int] = None
    alert_id: Optional[int] = None
    action_type: str  # BLOCK_IP, ISOLATE_HOST, RESTRICT_ACCOUNT, NOTIFY_ANALYST
    target: str


class ResponseActionApproval(BaseModel):
    action: str = "APPROVE"  # APPROVE, REJECT
    comments: Optional[str] = None


class ResponseActionOut(BaseModel):
    id: int
    action_uuid: str
    incident_id: Optional[int] = None
    alert_id: Optional[int] = None
    action_type: str
    target: str
    status: str
    requested_by_user_id: Optional[int] = None
    approved_by_user_id: Optional[int] = None
    execution_result: Optional[Dict[str, Any]] = None
    rollback_available: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== Threat Intelligence Schemas ====================

class ThreatIndicatorCreate(BaseModel):
    indicator_type: str  # IP, DOMAIN, HASH
    value: str
    threat_type: str
    severity: str = "HIGH"
    confidence: int = 80
    source: str = "SentinelLab"
    is_active: bool = True
    expires_at: Optional[datetime] = None


class ThreatIndicatorOut(ThreatIndicatorCreate):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== Audit Log Schemas ====================

class AuditLogOut(BaseModel):
    id: int
    user_id: Optional[int] = None
    username: Optional[str] = None
    action: str
    target_type: Optional[str] = None
    target_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True


# ==================== Analytics Schemas ====================

class SOCSummaryOut(BaseModel):
    total_events: int
    total_alerts: int
    critical_alerts: int
    active_incidents: int
    resolved_incidents: int
    monitored_endpoints: int
    threat_distribution: Dict[str, int]
    severity_distribution: Dict[str, int]
    recent_events_trend: List[Dict[str, Any]]
    ml_health_status: str


class NetworkAnalyticsOut(BaseModel):
    total_connections: int
    top_source_ips: List[Dict[str, Any]]
    top_dest_ports: List[Dict[str, Any]]
    protocols_breakdown: Dict[str, int]
    bandwidth_usage: Dict[str, Any]
