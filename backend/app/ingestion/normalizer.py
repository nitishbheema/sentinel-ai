import hashlib
import json
from datetime import datetime, timezone
from typing import Dict, Any, Tuple, Optional


def compute_event_hash(
    event_source: str,
    event_type: str,
    timestamp: datetime,
    source_ip: Optional[str],
    destination_ip: Optional[str],
    source_port: Optional[int],
    destination_port: Optional[int],
    process_name: Optional[str] = None
) -> str:
    raw_str = f"{event_source}|{event_type}|{timestamp.isoformat()}|{source_ip or ''}|{destination_ip or ''}|{source_port or ''}|{destination_port or ''}|{process_name or ''}"
    return hashlib.sha256(raw_str.encode("utf-8")).hexdigest()


def parse_timestamp(ts: Any) -> datetime:
    if isinstance(ts, datetime):
        if ts.tzinfo is None:
            return ts.replace(tzinfo=timezone.utc)
        return ts
    if isinstance(ts, (int, float)):
        return datetime.fromtimestamp(ts, tz=timezone.utc)
    if isinstance(ts, str):
        try:
            # ISO 8601 or similar
            cleaned = ts.replace("Z", "+00:00")
            return datetime.fromisoformat(cleaned)
        except Exception:
            pass
    return datetime.now(timezone.utc)


def normalize_zeek_log(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalizes Zeek conn or dns log into common schema
    """
    ts = parse_timestamp(data.get("ts", datetime.now(timezone.utc)))
    src_ip = data.get("id_orig_h") or data.get("id.orig_h")
    src_port = data.get("id_orig_p") or data.get("id.orig_p")
    dst_ip = data.get("id_resp_h") or data.get("id.resp_h")
    dst_port = data.get("id_resp_p") or data.get("id.resp_p")
    proto = (data.get("proto") or "TCP").upper()
    service = data.get("service") or "unknown"
    duration = float(data.get("duration") or 0.0)
    orig_bytes = int(data.get("orig_bytes") or 0)
    resp_bytes = int(data.get("resp_bytes") or 0)
    conn_state = data.get("conn_state") or "SF"

    normalized = {
        "event_source": "zeek",
        "event_type": f"zeek_{service}" if service != "unknown" else "zeek_conn",
        "timestamp": ts,
        "source_ip": str(src_ip) if src_ip else None,
        "source_port": int(src_port) if src_port else None,
        "destination_ip": str(dst_ip) if dst_ip else None,
        "destination_port": int(dst_port) if dst_port else None,
        "protocol": proto,
        "host_id": str(src_ip) if src_ip else "network_sensor",
        "username": None,
        "process_name": None,
        "process_pid": None,
        "normalized_data": {
            "duration": duration,
            "orig_bytes": orig_bytes,
            "resp_bytes": resp_bytes,
            "conn_state": conn_state,
            "service": service,
            "uid": data.get("uid")
        },
        "raw_data": data
    }
    normalized["hash_checksum"] = compute_event_hash(
        normalized["event_source"],
        normalized["event_type"],
        ts,
        normalized["source_ip"],
        normalized["destination_ip"],
        normalized["source_port"],
        normalized["destination_port"]
    )
    return normalized


def normalize_suricata_eve(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalizes Suricata EVE JSON alerts into common schema
    """
    ts = parse_timestamp(data.get("timestamp", datetime.now(timezone.utc)))
    src_ip = data.get("src_ip")
    src_port = data.get("src_port")
    dst_ip = data.get("dest_ip")
    dst_port = data.get("dest_port")
    proto = (data.get("proto") or "TCP").upper()
    alert_info = data.get("alert", {})
    signature = alert_info.get("signature", "Suricata Alert")
    severity = alert_info.get("severity", 2)
    category = alert_info.get("category", "Network Intrusion")

    normalized = {
        "event_source": "suricata",
        "event_type": "suricata_alert",
        "timestamp": ts,
        "source_ip": str(src_ip) if src_ip else None,
        "source_port": int(src_port) if src_port else None,
        "destination_ip": str(dst_ip) if dst_ip else None,
        "destination_port": int(dst_port) if dst_port else None,
        "protocol": proto,
        "host_id": str(dst_ip) if dst_ip else "network_sensor",
        "username": None,
        "process_name": None,
        "process_pid": None,
        "normalized_data": {
            "signature": signature,
            "category": category,
            "suricata_severity": severity,
            "signature_id": alert_info.get("signature_id")
        },
        "raw_data": data
    }
    normalized["hash_checksum"] = compute_event_hash(
        normalized["event_source"],
        normalized["event_type"],
        ts,
        normalized["source_ip"],
        normalized["destination_ip"],
        normalized["source_port"],
        normalized["destination_port"]
    )
    return normalized


def normalize_endpoint_event(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalizes Linux/Windows endpoint telemetry events
    """
    ts = parse_timestamp(data.get("timestamp", datetime.now(timezone.utc)))
    hostname = data.get("hostname", "unknown-host")
    ip_addr = data.get("ip_address")
    event_type = data.get("event_type", "endpoint_activity")
    username = data.get("username")
    proc_name = data.get("process_name")
    pid = data.get("pid")
    parent_pid = data.get("parent_pid")
    details = data.get("details", {})

    dest_ip = details.get("destination_ip")
    dest_port = details.get("destination_port")
    src_port = details.get("source_port")
    proto = details.get("protocol", "TCP")

    normalized = {
        "event_source": "endpoint",
        "event_type": event_type,
        "timestamp": ts,
        "source_ip": ip_addr,
        "source_port": src_port,
        "destination_ip": dest_ip,
        "destination_port": dest_port,
        "protocol": proto,
        "host_id": hostname,
        "username": username,
        "process_name": proc_name,
        "process_pid": pid,
        "normalized_data": {
            "parent_pid": parent_pid,
            "details": details
        },
        "raw_data": data
    }
    normalized["hash_checksum"] = compute_event_hash(
        normalized["event_source"],
        normalized["event_type"],
        ts,
        normalized["source_ip"],
        normalized["destination_ip"],
        normalized["source_port"],
        normalized["destination_port"],
        proc_name
    )
    return normalized
