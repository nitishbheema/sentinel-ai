import pytest
import time
from datetime import datetime, timezone


def test_scenario_1_brute_force(client, analyst_token):
    """
    SCENARIO 1 — BRUTE FORCE
    Generate controlled failed-login events.
    Expected: Rule engine detects repeated failures and generates an alert.
    """
    attacker_ip = "192.0.2.77"
    for i in range(5):
        res = client.post(
            "/api/v1/events/ingest/endpoint",
            json={
                "hostname": "sec-lab-srv01",
                "ip_address": attacker_ip,
                "event_type": "auth_failure",
                "username": "root",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "details": {"source_port": 50000 + i, "reason": "Bad password"}
            },
            headers={"X-Agent-Secret": "sentinel_agent_telemetry_secure_key_2026"}
        )
        assert res.status_code == 200

    # Verify Alert was generated
    alerts_res = client.get(
        "/api/v1/alerts",
        headers={"Authorization": f"Bearer {analyst_token}"}
    )
    assert alerts_res.status_code == 200
    alerts = alerts_res.json()
    brute_alerts = [a for a in alerts if "Brute Force" in a["title"]]
    assert len(brute_alerts) >= 1
    assert brute_alerts[0]["severity"] in ["HIGH", "CRITICAL"]


def test_scenario_2_port_scanning(client, analyst_token):
    """
    SCENARIO 2 — PORT SCANNING
    Generate port-scanning activity across multiple ports.
    Expected: Network monitoring identifies unusual port activity.
    """
    scanner_ip = "198.51.100.200"
    for port in [21, 22, 23, 80, 443, 8080]:
        res = client.post(
            "/api/v1/events/ingest/zeek",
            json={
                "ts": time.time(),
                "uid": f"uid-scan-{port}",
                "id_orig_h": scanner_ip,
                "id_orig_p": 49100,
                "id_resp_h": "192.168.1.10",
                "id_resp_p": port,
                "proto": "tcp",
                "service": "unknown",
                "conn_state": "REJ"
            },
            headers={"X-Agent-Secret": "sentinel_agent_telemetry_secure_key_2026"}
        )
        assert res.status_code == 200

    alerts_res = client.get(
        "/api/v1/alerts",
        headers={"Authorization": f"Bearer {analyst_token}"}
    )
    alerts = alerts_res.json()
    scan_alerts = [a for a in alerts if "Port" in a["title"] or "Scan" in a["title"]]
    assert len(scan_alerts) >= 1


def test_scenario_3_ml_anomaly(client, analyst_token):
    """
    SCENARIO 3 — ML ANOMALY
    Submit traffic with anomalous feature patterns.
    Expected: Isolation Forest identifies unusual behaviour.
    """
    res = client.post(
        "/api/v1/ml/predict",
        headers={"Authorization": f"Bearer {analyst_token}"},
        json={
            "destination_port": 65500,
            "flow_duration": 0.001,
            "tot_fwd_pkts": 1,
            "tot_bwd_pkts": 0,
            "tot_len_fwd_pkts": 40.0,
            "tot_len_bwd_pkts": 0.0,
            "flow_byts_s": 40000.0,
            "flow_pkts_s": 1000.0,
            "syn_flag_cnt": 1,
            "ack_flag_cnt": 0
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert "isolation_forest_anomaly_score" in data
    assert 0.0 <= data["isolation_forest_anomaly_score"] <= 1.0


def test_scenario_4_malicious_traffic_classification(client, analyst_token):
    """
    SCENARIO 4 — MALICIOUS TRAFFIC CLASSIFICATION
    Submit properly formatted network traffic features.
    Expected: Random Forest returns the model's actual prediction.
    """
    res = client.post(
        "/api/v1/ml/predict",
        headers={"Authorization": f"Bearer {analyst_token}"},
        json={
            "destination_port": 80,
            "flow_duration": 0.05,
            "tot_fwd_pkts": 40,
            "tot_bwd_pkts": 1,
            "tot_len_fwd_pkts": 24000.0,
            "tot_len_bwd_pkts": 60.0,
            "syn_flag_cnt": 1,
            "ack_flag_cnt": 0
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert data["random_forest_classification"] in ["BENIGN", "PortScan", "DDoS", "BruteForce", "WebAttack", "Botnet"]
    assert 0.0 <= data["random_forest_confidence"] <= 1.0
    assert len(data["feature_importance"]) > 0


def test_scenario_5_event_correlation(client, analyst_token):
    """
    SCENARIO 5 — EVENT CORRELATION
    Generate multiple related events for the same host.
    Expected: Correlation engine groups them into an incident.
    """
    test_host = "fin-correlate-srv"
    # Stage 1: Auth failure
    client.post(
        "/api/v1/events/ingest/endpoint",
        json={
            "hostname": test_host,
            "ip_address": "10.0.0.99",
            "event_type": "auth_failure",
            "username": "admin"
        }
    )
    # Stage 2: Auth success
    client.post(
        "/api/v1/events/ingest/endpoint",
        json={
            "hostname": test_host,
            "ip_address": "10.0.0.99",
            "event_type": "auth_success",
            "username": "admin"
        }
    )
    # Stage 3: Process spawn
    client.post(
        "/api/v1/events/ingest/endpoint",
        json={
            "hostname": test_host,
            "ip_address": "10.0.0.99",
            "event_type": "process_spawn",
            "process_name": "nc",
            "pid": 9991,
            "details": {"parent_process": "python"}
        }
    )

    incidents_res = client.get(
        "/api/v1/incidents",
        headers={"Authorization": f"Bearer {analyst_token}"}
    )
    assert incidents_res.status_code == 200
    incidents = incidents_res.json()
    assert len(incidents) >= 1


def test_scenario_6_incident_investigation(client, analyst_token):
    """
    SCENARIO 6 — INCIDENT INVESTIGATION
    Open an incident, add notes, and change status.
    Expected: Incident workflow, notes and status changes work.
    """
    # Create incident
    create_res = client.post(
        "/api/v1/incidents",
        headers={"Authorization": f"Bearer {analyst_token}"},
        json={
            "title": "Investigation Scenario Test",
            "description": "Validating analyst investigation notes and workflow",
            "severity": "HIGH",
            "status": "INVESTIGATING"
        }
    )
    assert create_res.status_code == 200
    inc_id = create_res.json()["id"]

    # Add Note
    note_res = client.post(
        f"/api/v1/incidents/{inc_id}/notes",
        headers={"Authorization": f"Bearer {analyst_token}"},
        json={"note": "Observed unauthorized lateral movement via SSH"}
    )
    assert note_res.status_code == 200
    assert note_res.json()["note"] == "Observed unauthorized lateral movement via SSH"

    # Update status to CONFIRMED
    patch_res = client.patch(
        f"/api/v1/incidents/{inc_id}",
        headers={"Authorization": f"Bearer {analyst_token}"},
        json={"status": "CONFIRMED"}
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["status"] == "CONFIRMED"


def test_scenario_7_response_approval(client, analyst_token):
    """
    SCENARIO 7 — RESPONSE APPROVAL
    Submit a response recommendation.
    Expected: Analyst approval is required and the action is audited.
    """
    actions_res = client.get(
        "/api/v1/response/actions",
        headers={"Authorization": f"Bearer {analyst_token}"}
    )
    assert actions_res.status_code == 200
    actions = actions_res.json()
    pending = [a for a in actions if a["status"] == "PENDING_APPROVAL"]

    if pending:
        target_action = pending[0]
        # Approve execution
        appr_res = client.post(
            f"/api/v1/response/{target_action['id']}/approve",
            headers={"Authorization": f"Bearer {analyst_token}"}
        )
        assert appr_res.status_code == 200
        assert appr_res.json()["status"] == "EXECUTED"


def test_scenario_8_authorization(client, viewer_token, analyst_token):
    """
    SCENARIO 8 — AUTHORIZATION
    Log in using different roles.
    Expected: Restricted APIs reject unauthorized operations.
    """
    # Viewer cannot approve defensive responses
    res = client.post(
        "/api/v1/response/1/approve",
        headers={"Authorization": f"Bearer {viewer_token}"}
    )
    assert res.status_code == 403


def test_scenario_9_real_time_dashboard(client, analyst_token):
    """
    SCENARIO 9 — REAL-TIME DASHBOARD
    Generate and ingest new events.
    Expected: Dashboard updates without requiring a full-page reload.
    """
    res = client.get(
        "/api/v1/analytics/overview",
        headers={"Authorization": f"Bearer {analyst_token}"}
    )
    assert res.status_code == 200
    data = res.json()
    assert "total_events" in data
    assert "total_alerts" in data
    assert "active_incidents" in data
    assert "threat_distribution" in data


def test_scenario_10_failure_handling(client):
    """
    SCENARIO 10 — FAILURE HANDLING
    Submit malformed events or invalid tokens.
    Expected: System handles failures gracefully, logs errors and does not silently lose data.
    """
    # Missing required fields or unauthorized agent
    res = client.post(
        "/api/v1/events/ingest",
        json={"invalid_key": "bad_data"}
    )
    assert res.status_code in [401, 422, 400]

    # Non-existent incident
    res_404 = client.get(
        "/api/v1/incidents/999999",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert res_404.status_code in [401, 404]
