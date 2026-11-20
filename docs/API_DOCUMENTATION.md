# SentinelAI API Documentation

## 1. Overview & Base URL

The SentinelAI platform exposes a comprehensive, RESTful API versioned under `/api/v1`.
- **Default Base URL**: `http://localhost:8000/api/v1`
- **Interactive Documentation**:
  - Swagger UI: `http://localhost:8000/docs`
  - ReDoc: `http://localhost:8000/redoc`

All requests and responses use JSON format (`Content-Type: application/json`).

---

## 2. Authentication & Authorization

SentinelAI utilizes JSON Web Tokens (JWT) using the HMAC-SHA256 (`HS256`) algorithm.

### Headers
For authenticated endpoints, include the token in the `Authorization` header:
```http
Authorization: Bearer <access_token>
```

For endpoint agent event submissions, use the `X-Agent-Key` header:
```http
X-Agent-Key: <agent_api_key>
```

### Role-Based Access Control (RBAC)
SentinelAI defines three standard roles:
- **`ADMIN`**: Full platform control, user provisioning, rule toggling, response action approvals.
- **`ANALYST`**: Event monitoring, alert triage, incident investigation, response action initiation.
- **`VIEWER`**: Read-only access to dashboards, alerts, metrics, and audit records.

---

## 3. Endpoints

### 3.1 Authentication (`/auth`)

#### `GET /auth/setup-status`
Returns whether first-time administrator initialization is required.
- **Success Response (200 OK)**:
  ```json
  {
    "setup_required": false,
    "user_count": 1,
    "message": "Platform already provisioned."
  }
  ```

#### `POST /auth/setup-admin`
Provisions the initial root administrator account. Fails with 403 Forbidden once any user exists.
- **Request Body**:
  ```json
  {
    "username": "secadmin",
    "email": "admin@yourdomain.com",
    "password": "SecurePassword1234!"
  }
  ```

#### `POST /auth/login`
Authenticates a user and returns access and refresh tokens. Rate-limited to 5 requests/min.
- **Request Body**:
  ```json
  {
    "username": "secadmin",
    "password": "SecurePassword1234!"
  }
  ```
- **Success Response (200 OK)**:
  ```json
  {
    "access_token": "eyJhbGciOi...",
    "refresh_token": "eyJhbGciOi...",
    "token_type": "bearer",
    "role": "ADMIN",
    "username": "admin"
  }
  ```

#### `POST /auth/refresh`
Refreshes an expired access token using a valid refresh token.
- **Request Query**: `?refresh_token=<token>`
- **Success Response (200 OK)**:
  ```json
  {
    "access_token": "eyJhbGciOi...",
    "token_type": "bearer"
  }
  ```

#### `GET /auth/me`
Retrieves profile information for the authenticated user.
- **Success Response (200 OK)**:
  ```json
  {
    "id": 1,
    "username": "admin",
    "email": "admin@sentinelai.local",
    "role": "ADMIN",
    "is_active": true
  }
  ```

---

### 3.2 Event Ingestion (`/events`)

#### `POST /events/ingest`
Ingests a single or batch of endpoint or sensor events.
- **Authentication**: JWT or `X-Agent-Key`
- **Request Body**:
  ```json
  {
    "event_id": "c1f7a0b5-7798-4444-a957-695fbcf65311",
    "timestamp": "2026-11-18T10:00:00Z",
    "source_type": "ENDPOINT",
    "event_type": "AUTH_FAILED",
    "host_id": "endpoint-linux-01",
    "source_ip": "192.168.1.105",
    "destination_ip": "192.168.1.20",
    "user_identity": "root",
    "process_name": "/usr/sbin/sshd",
    "payload": {
      "method": "password",
      "attempt": 1
    }
  }
  ```
- **Success Response (201 Created)**:
  ```json
  {
    "status": "ACCEPTED",
    "event_id": "c1f7a0b5-7798-4444-a957-695fbcf65311",
    "deduplicated": false,
    "stored_id": 142
  }
  ```

#### `GET /events/`
Queries normalized security events with filtering and pagination.
- **Query Parameters**:
  - `limit` (default 50)
  - `offset` (default 0)
  - `source_type` (e.g., `ZEEK`, `SURICATA`, `ENDPOINT`)
  - `event_type` (e.g., `AUTH_FAILED`, `NETWORK_FLOW`, `PORT_SCAN`)
  - `source_ip`
- **Success Response (200 OK)**:
  ```json
  {
    "total": 1,
    "events": [...]
  }
  ```

---

### 3.3 Security Alerts (`/alerts`)

#### `GET /alerts/`
List security alerts filtered by severity, status, or date range.
- **Query Parameters**: `severity` (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`), `status` (`NEW`, `TRIAGED`, `DISMISSED`)
- **Success Response (200 OK)**:
  ```json
  [
    {
      "id": 1,
      "alert_id": "alt-b295da93",
      "title": "Brute Force Authentication Detected",
      "severity": "HIGH",
      "risk_score": 75.0,
      "status": "NEW",
      "source_ip": "192.168.1.105",
      "mitre_technique": "T1110",
      "created_at": "2026-11-18T10:00:30Z"
    }
  ]
  ```

#### `GET /alerts/{id}`
Returns granular alert details, including ML feature explanations and triggered rule conditions.

---

### 3.4 Incident Management (`/incidents`)

#### `GET /incidents/`
Returns all security incidents with status, priority, and assigned analyst.

#### `POST /incidents/`
Manually create an incident or escalate an alert into an incident.
- **Request Body**:
  ```json
  {
    "title": "Suspected Lateral Movement - Host 192.168.1.105",
    "description": "Multi-stage attack involving failed logins followed by port sweep",
    "severity": "CRITICAL",
    "assigned_to": 2
  }
  ```

#### `PATCH /incidents/{id}`
Updates incident status (`NEW`, `INVESTIGATING`, `CONFIRMED`, `RESOLVED`, `FALSE_POSITIVE`).

#### `POST /incidents/{id}/notes`
Adds an investigation journal entry or analyst comment.

---

### 3.5 Automated Defense & Response (`/response`)

#### `GET /response/actions`
Lists all defensive response actions and their approval state (`PENDING_APPROVAL`, `APPROVED`, `EXECUTED`, `REJECTED`, `ROLLED_BACK`).

#### `POST /response/actions`
Requests a defensive action.
- **Request Body**:
  ```json
  {
    "action_type": "BLOCK_IP",
    "target": "203.0.113.55",
    "incident_id": 1,
    "justification": "Malicious C2 node sending brute-force requests"
  }
  ```

#### `POST /response/actions/{id}/approve`
**Requires `ADMIN` role.** Approves and executes defensive action.

#### `POST /response/actions/{id}/rollback`
**Requires `ADMIN` role.** Reverses the executed containment action.

---

### 3.6 Machine Learning Inference (`/ml`)

#### `POST /ml/predict`
Direct flow evaluation through Random Forest classifier and Isolation Forest anomaly detector.
- **Request Body**:
  ```json
  {
    "destination_port": 80,
    "flow_duration": 120000,
    "tot_fwd_pkts": 5,
    "tot_bwd_pkts": 4,
    "tot_len_fwd_pkts": 450,
    "tot_len_bwd_pkts": 3200,
    "flow_byts_s": 25000.0,
    "flow_pkts_s": 75.0,
    "flow_iat_mean": 15000.0,
    "fwd_pkt_len_max": 200,
    "fwd_pkt_len_min": 40,
    "fwd_pkt_len_mean": 90.0,
    "fwd_pkt_len_std": 12.5,
    "fwd_iat_tot": 60000.0,
    "bwd_iat_tot": 60000.0,
    "psh_flag_cnt": 1,
    "ack_flag_cnt": 1,
    "syn_flag_cnt": 0,
    "rst_flag_cnt": 0
  }
  ```
- **Success Response (200 OK)**:
  ```json
  {
    "rf_prediction": "BENIGN",
    "rf_confidence": 0.985,
    "anomaly_score": 0.042,
    "is_anomaly": false,
    "top_contributing_features": {
      "fwd_pkt_len_max": 0.209,
      "tot_len_bwd_pkts": 0.122
    }
  }
  ```

#### `GET /ml/metrics`
Returns current model accuracy, precision, recall, F1 score, confusion matrix, and feature importances.

---

### 3.7 Analytics & Dashboards (`/analytics`)

#### `GET /analytics/dashboard`
Returns aggregated metrics for the SOC dashboard:
- 24-hour event volumes and timeline series.
- Active alert distribution by severity (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`).
- Incident progression metrics.
- Top targeted hosts and top offending remote IPs.
- Detection source breakdown (Zeek, Suricata, Endpoint).

---

### 3.8 Detection Rules (`/rules`)

#### `GET /rules/`
Lists all Sigma-inspired rules with rule ID, name, severity, enabled status, and version.

#### `PATCH /rules/{id}/toggle`
Enables or disables a specific detection rule.

---

### 3.9 Threat Intelligence (`/threat-intel`)

#### `GET /threat-intel/indicators`
Lists locally cached indicators of compromise (IOCs).

#### `POST /threat-intel/indicators`
Registers a new threat indicator (IP, domain, or hash) with confidence rating and source attribution.

#### `POST /threat-intel/lookup`
Performs immediate reputation check for an IP or domain against the intelligence database.

---

### 3.10 System Audit Log (`/audit`)

#### `GET /audit/`
**Requires `ADMIN` or `ANALYST` role.** Returns tamper-evident audit logs capturing user actions, configuration changes, and approval events.
