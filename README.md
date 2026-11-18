# SentinelAI: Intelligent Threat Detection & Autonomous SOC Response Platform

SentinelAI is an enterprise-grade Security Operations Center (SOC) telemetry processing, threat detection, and incident response platform. It combines deterministic Sigma-inspired detection rules with machine learning models and multi-stage temporal correlation to detect, investigate, and mitigate cyber threats.

---

## Architecture Overview

SentinelAI uses a layered architecture separating collection, ingestion, detection, and analysis:

1. **Telemetry & Sensor Ingestion**:
   - Python-based cross-platform endpoint monitoring agent.
   - Zeek network connection metadata parser.
   - Suricata EVE JSON signature alert parser.
   - Schema normalization, hash verification, and idempotency deduplication.

2. **Detection & Analytics**:
   - **Sigma-Style Rules**: Configurable YAML rules with sliding time windows and alert flood suppression.
   - **Supervised ML Classifier**: Random Forest model trained on 19 network flow attributes (CICIDS2017 schema).
   - **Unsupervised Anomaly Detector**: Isolation Forest model trained on benign baseline network traffic.
   - **Multi-Stage Attack Correlator**: Graph and time-series association linking discrete events across the MITRE ATT&CK matrix.
   - **Risk Scoring**: Composite 0–100 threat scoring combining rules, ML, temporal correlation, and threat intelligence.

3. **Incident Response & Triage**:
   - Structured incident lifecycle management (`NEW`, `INVESTIGATING`, `CONFIRMED`, `RESOLVED`, `FALSE_POSITIVE`).
   - Analyst-controlled containment actions (`BLOCK_IP`, `ISOLATE_HOST`) with rollback support.
   - Role-Based Access Control (RBAC) with granular `ADMIN`, `ANALYST`, and `VIEWER` roles.
   - Complete audit logging of all analyst decisions.

4. **Web Interface**:
   - React 18 single-page application styled with Tailwind CSS.
   - Real-time telemetry monitoring, interactive investigation timelines, and threat analytics charts.

---

## Directory Structure

```text
SentineIAI/
├── agents/                   # Endpoint agents and network sensor parsers
│   ├── endpoint_agent/       # Python host telemetry agent
│   └── network_sensor/       # Zeek and Suricata log collectors
├── backend/                  # FastAPI backend server
│   ├── app/
│   │   ├── api/v1/           # REST API endpoints & route controllers
│   │   ├── core/             # Configuration, logging, and security
│   │   ├── correlation/      # Temporal attack correlation engine
│   │   ├── database/         # SQLAlchemy models, sessions, and seeds
│   │   ├── detection/        # Sigma rule runner & ML inference service
│   │   ├── schemas/          # Pydantic validation models
│   │   ├── threat_intelligence/ # Local IOC cache and matcher
│   │   └── workers/          # Async event processing pipeline
│   ├── detection-rules/      # Sigma-style detection rules (YAML)
│   ├── migrations/           # Alembic database migration scripts
│   └── tests/                # Pytest suites for auth and acceptance scenarios
├── docs/                     # Architectural and technical documentation
├── frontend/                 # React 18 + Vite + Tailwind CSS dashboard
├── infrastructure/           # Nginx reverse proxy configurations
├── ml-engine/                # ML pipelines, training scripts, and models
└── docker-compose.yml        # Multi-container orchestration specification
```

---

## Default Access Credentials

The initial database seed provisions three standard testing accounts:

| Username | Password | Role | Scope |
| :--- | :--- | :--- | :--- |
| `admin` | `SentinelAdmin2026!` | `ADMIN` | Full administrative control and containment approval |
| `analyst` | `SentinelAnalyst2026!` | `ANALYST` | Incident triage, investigation notes, and containment requests |
| `viewer` | `SentinelViewer2026!` | `VIEWER` | Read-only access to dashboards, alerts, and metrics |

---

## Quickstart

### Option 1: Docker Compose

```bash
# Clone the repository
git clone https://github.com/your-org/sentinelai.git
cd sentinelai

# Start containers
docker-compose up -d --build
```

- Frontend: `http://localhost`
- Backend API: `http://localhost:8000`
- API Documentation: `http://localhost:8000/docs`

### Option 2: Local Development Setup

#### Backend:
```bash
cd backend
python -m venv venv
# Activate virtual environment (. .\venv\Scripts\Activate.ps1 or source venv/bin/activate)
pip install -r requirements.txt
alembic upgrade head
python -c "from app.database.init_db import init_db; from app.database.session import SessionLocal; init_db(SessionLocal())"
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Frontend:
```bash
cd frontend
npm install
npm run dev
```

---

## Automated Testing

Execute the test suite verifying all 10 core detection and incident response scenarios:

```bash
cd backend
pytest tests/ -v
```

All 13 acceptance and security test cases validate against live SQLite or PostgreSQL database engines.
