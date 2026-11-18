# SentinelAI Threat Model & Security Architecture

## 1. Executive Summary

SentinelAI is an intelligent Security Operations Center (SOC) platform designed to ingest telemetry from distributed network sensors and endpoint monitoring agents, analyze data via rule-based and machine-learning engines, correlate multi-stage attacks, and orchestrate defensive containment actions.

Because SentinelAI acts as a defensive command-and-control platform, its security architecture and trust boundaries must be rigorously defined to prevent adversary tampering, ingestion spoofing, denial of service, privilege escalation, or unauthorized automated containment.

---

## 2. Threat Actors & Capabilities

| Threat Actor | Motivation | Assumed Capabilities | Target Assets |
| :--- | :--- | :--- | :--- |
| **External Cybercriminal / APT** | Financial gain, espionage, ransomware deployment | Network scanning, brute force, C2 beaconing, payload delivery, obfuscation | Corporate endpoints, confidential databases, credential stores |
| **Malicious Insider / Compromised Host** | Data exfiltration, sabotage, lateral movement | Internal network access, compromised workstation credentials | Active Directory, internal servers, SentinelAI ingestion APIs |
| **Adversary Targeting SOC Infrastructure** | Evading detection, disabling defenses, telemetry blindspots | Log flooding, agent spoofing, adversarial ML evasion, alert fatigue generation | SentinelAI API, Redis task queues, ML inference pipeline, response actuators |

---

## 3. Trust Boundaries & Data Flow

```
                      +---------------------------------------+
                      |       UNTRUSTED / EXTERNAL            |
                      |  Internet, Threat Actors, External IP  |
                      +-------------------+-------------------+
                                          | Network Packets / Probes
                                          v
                      +---------------------------------------+
                      |         MONITORED PERIMETER           |
                      |   Endpoints, Linux Hosts, DMZ         |
                      |   [Zeek Sensor]   [Suricata Sensor]   |
                      |   [SentinelAI Python Endpoint Agent]  |
                      +-------------------+-------------------+
                                          |
                      ============= TRUST BOUNDARY 1: INGESTION =============
                                          | HTTPS + Agent Key Authentication
                                          v
                      +---------------------------------------+
                      |        SENTINELAI INGESTION & CORE    |
                      |   FastAPI REST APIs (TLS Encrypted)   |
                      |   Schema Validation & Deduplication   |
                      |   Redis Background Worker Queue       |
                      +-------------------+-------------------+
                                          |
                      ============= TRUST BOUNDARY 2: INTERNAL BUS ==========
                                          | Internal IPC / Worker Task Dispatch
                                          v
                      +---------------------------------------+
                      |     DETECTION & CORRELATION LAYER     |
                      |   Sigma Rule Engine                   |
                      |   Random Forest & Isolation Forest ML |
                      |   Temporal Attack Correlator          |
                      |   Risk Engine (0-100 Score)           |
                      +-------------------+-------------------+
                                          |
                      ============= TRUST BOUNDARY 3: PERSISTENCE ===========
                                          | Authenticated Database Pool
                                          v
                      +---------------------------------------+
                      |           DATA STORAGE LAYER          |
                      |   PostgreSQL / SQLite Database        |
                      |   Encrypted JSONB Event Payloads      |
                      |   Audit Logs & Response Records       |
                      +-------------------+-------------------+
                                          ^
                                          | JWT RBAC Authentication
                      ============= TRUST BOUNDARY 4: PRESENTATION ==========
                                          |
                      +---------------------------------------+
                      |            SOC OPERATOR UI            |
                      |   React 18 Dashboard (TLS)            |
                      |   Roles: ADMIN / ANALYST / VIEWER     |
                      +---------------------------------------+
```

---

## 4. STRIDE Threat Analysis

### 4.1 Spoofing
- **Threat**: An adversary registers a fake endpoint agent or transmits forged telemetry with falsified timestamps or IP addresses to frame benign hosts.
- **Mitigation**:
  - Endpoint agents authenticate using pre-shared HMAC agent keys (`X-Agent-Key`).
  - Web users authenticate via Argon2-hashed credentials and HS256 JWT tokens.
  - Event schemas enforce cryptographic hash generation (`SHA-256(host_id + timestamp + event_type + payload)`) and reject duplicate hashes.

### 4.2 Tampering
- **Threat**: An attacker alters historical event records or modifies detection rule configurations to blind the SOC.
- **Mitigation**:
  - Immutable event log design in relational storage.
  - Dedicated `audit_logs` table tracking rule modification, role changes, and containment triggers.
  - Rule files versioned and validated against Sigma schema definitions.

### 4.3 Repudiation
- **Threat**: An operator or analyst initiates a disruptive network isolation and denies responsibility.
- **Mitigation**:
  - Strict Role-Based Access Control (RBAC).
  - All defensive containment approvals (`APPROVE`, `ROLLBACK`) record the operator's user ID, IP address, and justification timestamp in the non-repudiable audit journal.

### 4.4 Information Disclosure
- **Threat**: Exposure of monitored system metadata, sensitive user passwords, or internal network topology via API errors or unencrypted communication.
- **Mitigation**:
  - The Python endpoint agent explicitly excludes passwords, keystroke logs, personal documents, and memory dumps.
  - API responses strip raw traceback information in production.
  - Strong password hashing (Argon2 / bcrypt) with salt.

### 4.5 Denial of Service (DoS)
- **Threat**: An adversary floods the event ingestion API with millions of dummy connection records to exhaust database connections and memory.
- **Mitigation**:
  - Asynchronous event queuing decoupling ingestion from ML inference.
  - Sliding-window rule evaluation with anti-flooding suppression (maximum alert frequencies per unique source IP).
  - Ingestion rate-limiting and lightweight Pydantic schema validation before queue insertion.

### 4.6 Elevation of Privilege
- **Threat**: A read-only `VIEWER` or compromised `ANALYST` executes firewall modifications or isolates domain controllers.
- **Mitigation**:
  - Endpoint actions are locked to `ADMIN` approval only.
  - All destructive operations require dual-phase review (`PENDING_APPROVAL` status by default).
  - No automated unprompted containment without analyst-approved intervention.

---

## 5. Security Guardrails

1. **Human-in-the-Loop Containment**: No automated defensive command executes destructively on live networks without prior authorization by a verified human analyst.
2. **Model Poisoning & Concept Drift Defense**: Preprocessing parameters (Scalers, Encoders) are version-controlled and fit only on verified baseline datasets.
3. **Defense-in-Depth**: Rule-based detection provides deterministic zero-latency coverage for known attack signatures, while unsupervised Isolation Forest detects zero-day anomalous outliers.
