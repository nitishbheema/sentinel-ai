# SentinelAI System Architecture

## 1. High-Level Architecture Overview

SentinelAI is an enterprise-grade AI-powered Security Operations Centre (SOC) platform that monitors network telemetry and endpoint activity, identifies threats using rule-based heuristics and machine learning models, correlates multi-stage attack chains, calculates explainable threat risk scores (0–100), and provides an analyst-approved defensive response workflow.

```mermaid
flowchart TD
    subgraph SENSORS["Sensors & Telemetry"]
        A1["Zeek Network Sensor<br/>(conn.log, dns.log, http.log)"]
        A2["Suricata IDS Sensor<br/>(eve.json Alerts & Flows)"]
        A3["Sentinel Linux/Windows Agent<br/>(Auth, Processes, Network, Files)"]
    end

    subgraph INGESTION["FastAPI Ingestion & Normalization Layer"]
        B1["/api/v1/events/ingest/*"]
        B2["Canonical Event Normalizer & SHA-256 Deduplication"]
    end

    subgraph DETECTION["Detection & Analytics Engine"]
        C1["Sigma-Inspired Rule Engine<br/>(Sliding Time Windows & Heuristics)"]
        C2["Supervised Random Forest<br/>(CICIDS2017 Classifier: 97.25% Acc)"]
        C3["Unsupervised Isolation Forest<br/>(Network Anomaly Detector)"]
        C4["Threat Intelligence Matcher<br/>(Local IP/Domain/Hash IOC Hub)"]
    end

    subgraph REASONING["Correlation & Risk Scoring"]
        D1["Multi-Stage Event Correlation Engine<br/>(Entity & Temporal Attack Chains)"]
        D2["Composite Risk Engine<br/>(0.35 ML + 0.30 Rule + 0.20 Corr + 0.15 Intel)"]
        D3["MITRE ATT&CK Mapping & Explainable AI (XAI)"]
    end

    subgraph STORAGE["Storage Layer"]
        E1[("PostgreSQL / SQLite Database<br/>(13 Relational Tables)")]
        E2[("Redis Queue / Cache")]
    end

    subgraph PRESENTATION["SOC Analyst Interface"]
        F1["React 18 + Vite SOC Dashboard<br/>(16 Interactive Views & Real-time Charts)"]
        F2["Analyst Investigation Workbench"]
        F3["Human-in-the-Loop Response Hub<br/>(IP Block, Host Quarantine, Rollback)"]
    end

    A1 --> B1
    A2 --> B1
    A3 --> B1
    B1 --> B2
    B2 --> C1
    B2 --> C2
    B2 --> C3
    B2 --> C4
    C1 --> D1
    C2 --> D1
    C3 --> D1
    C4 --> D1
    D1 --> D2
    D2 --> D3
    D3 --> E1
    E1 --> F1
    F1 --> F2
    F2 --> F3
    F3 -.->|Approval Audit| E1
```

---

## 2. Component Breakdown

### 2.1 Ingestion & Normalization Layer
- **FastAPI Endpoints**: High-throughput async endpoints receiving telemetry from Zeek, Suricata, and endpoint agents.
- **Canonical Schema**: Normalizes diverse sensor formats into a uniform model: `event_source`, `event_type`, `timestamp`, `source_ip`, `destination_ip`, `source_port`, `destination_port`, `protocol`, `host_id`, `username`, `process_name`, `process_pid`, `raw_data`, `normalized_data`.
- **Idempotency & Deduplication**: Generates deterministic SHA-256 checksums to reject duplicate logs within sliding windows.

### 2.2 Detection Engines
1. **Rule Engine**: Evaluates sliding windows and frequency thresholds using Sigma-inspired YAML rules (RULE-001 through RULE-008).
2. **Supervised Random Forest**: Trained on the calibrated CICIDS2017 intrusion benchmark (100 estimators, max depth 16) with 97.25% test accuracy.
3. **Unsupervised Isolation Forest**: Trained solely on benign baseline flows to flag anomalous feature shifts without requiring historical attack labels.
4. **Threat Intelligence Engine**: Matches telemetry against active indicators of compromise (IOCs) with severity weighting and expiry checks.

### 2.3 Event Correlation & Risk Scoring
- Correlates isolated events sharing common host, source IP, or user attributes within a 600-second window.
- Detects multi-stage attack chains (e.g. Brute Force -> Successful Authentication -> Shell Execution -> C2 Outbound Traffic).
- Automatically synthesizes incidents linked to primary event evidence.
- Calculates an explainable composite risk score from 0 to 100 with component weighting.

### 2.4 Human-in-the-Loop Defense Response
- Enforces strict analyst authorization before any containment command is dispatched.
- Demonstrates simulated host network isolation and IP drop rules in an isolated lab environment.
- Supports complete rollback of executed actions with immutable audit logging.
