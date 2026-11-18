from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user, require_roles, verify_agent_token, log_audit
from app.models.models import SecurityEvent, User
from app.schemas.schemas import (
    SecurityEventCreate,
    SecurityEventOut,
    IngestionResponse,
    ZeekConnLog,
    SuricataEveAlert,
    EndpointTelemetryEvent
)
from app.ingestion.normalizer import (
    normalize_zeek_log,
    normalize_suricata_eve,
    normalize_endpoint_event,
    compute_event_hash,
    parse_timestamp
)
from app.workers.processor import process_normalized_event

router = APIRouter()


@router.post("/ingest", response_model=IngestionResponse)
def ingest_generic_event(
    event_in: SecurityEventCreate,
    request: Request,
    db: Session = Depends(get_db),
    agent_auth: bool = Depends(verify_agent_token)
):
    ts = parse_timestamp(event_in.timestamp)
    norm = {
        "event_source": event_in.event_source,
        "event_type": event_in.event_type,
        "timestamp": ts,
        "source_ip": event_in.source_ip,
        "source_port": event_in.source_port,
        "destination_ip": event_in.destination_ip,
        "destination_port": event_in.destination_port,
        "protocol": event_in.protocol or "TCP",
        "host_id": event_in.host_id,
        "username": event_in.username,
        "process_name": event_in.process_name,
        "process_pid": event_in.process_pid,
        "raw_data": event_in.raw_data or {},
        "normalized_data": event_in.raw_data or {},
        "hash_checksum": compute_event_hash(
            event_in.event_source,
            event_in.event_type,
            ts,
            event_in.source_ip,
            event_in.destination_ip,
            event_in.source_port,
            event_in.destination_port,
            event_in.process_name
        )
    }

    result = process_normalized_event(norm, db)
    return {
        "status": result["status"],
        "event_id": result["event_id"],
        "event_uuid": result["event_uuid"],
        "detected_alerts": result.get("detected_alerts", 0),
        "message": "Event normalized and processed through detection pipeline"
    }


@router.post("/ingest/zeek", response_model=IngestionResponse)
def ingest_zeek_log(
    log_data: Dict[str, Any],
    db: Session = Depends(get_db),
    agent_auth: bool = Depends(verify_agent_token)
):
    normalized = normalize_zeek_log(log_data)
    result = process_normalized_event(normalized, db)
    return {
        "status": result["status"],
        "event_id": result["event_id"],
        "event_uuid": result["event_uuid"],
        "detected_alerts": result.get("detected_alerts", 0),
        "message": "Zeek log normalized and evaluated"
    }


@router.post("/ingest/suricata", response_model=IngestionResponse)
def ingest_suricata_alert(
    eve_alert: Dict[str, Any],
    db: Session = Depends(get_db),
    agent_auth: bool = Depends(verify_agent_token)
):
    normalized = normalize_suricata_eve(eve_alert)
    result = process_normalized_event(normalized, db)
    return {
        "status": result["status"],
        "event_id": result["event_id"],
        "event_uuid": result["event_uuid"],
        "detected_alerts": result.get("detected_alerts", 0),
        "message": "Suricata EVE alert ingested and evaluated"
    }


@router.post("/ingest/endpoint", response_model=IngestionResponse)
def ingest_endpoint_telemetry(
    endpoint_data: Dict[str, Any],
    db: Session = Depends(get_db),
    agent_auth: bool = Depends(verify_agent_token)
):
    normalized = normalize_endpoint_event(endpoint_data)
    result = process_normalized_event(normalized, db)
    return {
        "status": result["status"],
        "event_id": result["event_id"],
        "event_uuid": result["event_uuid"],
        "detected_alerts": result.get("detected_alerts", 0),
        "message": "Endpoint telemetry processed"
    }


@router.get("", response_model=List[SecurityEventOut])
def list_events(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    event_source: Optional[str] = None,
    event_type: Optional[str] = None,
    host_id: Optional[str] = None,
    source_ip: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(SecurityEvent)
    if event_source:
        query = query.filter(SecurityEvent.event_source == event_source)
    if event_type:
        query = query.filter(SecurityEvent.event_type == event_type)
    if host_id:
        query = query.filter(SecurityEvent.host_id == host_id)
    if source_ip:
        query = query.filter(SecurityEvent.source_ip == source_ip)

    return query.order_by(SecurityEvent.id.desc()).offset(skip).limit(limit).all()


@router.get("/{event_id}", response_model=SecurityEventOut)
def get_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    event = db.query(SecurityEvent).filter(SecurityEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event
