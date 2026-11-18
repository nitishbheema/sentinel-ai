# SentinelAI Deployment & Production Operations Guide

## 1. System Requirements

### Hardware Prerequisites
- **CPU**: 4 Cores recommended (Minimum 2 Cores for lab evaluation).
- **RAM**: 8 GB recommended (Minimum 4 GB).
- **Storage**: 20 GB free disk space for OS, container images, and telemetry storage.

### Software Prerequisites
- **Containerized**: Docker Engine 24.0+ and Docker Compose v2.20+.
- **Native Lab**:
  - Python 3.10+ (Tested on Python 3.11 / 3.12).
  - Node.js 18.0+ & npm 9.0+.
  - Optional: PostgreSQL 15+ and Redis 7.0+ (SQLite and in-process queuing supported for local standalone testing).

---

## 2. Containerized Deployment (Docker Compose)

SentinelAI provides a production-grade multi-container topology orchestrated via Docker Compose:

```
                  +---------------------------+
                  |    Nginx Reverse Proxy    |
                  |     Port 80 / 443         |
                  +-------------+-------------+
                                |
             +------------------+------------------+
             |                                     |
             v                                     v
+------------------------+             +------------------------+
|  React 18 Frontend UI  |             |  FastAPI Backend Core  |
|  Container: frontend   |             |  Container: backend    |
|  Port 80 (Internal)    |             |  Port 8000             |
+------------------------+             +-----------+------------+
                                                   |
             +-------------------------------------+-------------------------------------+
             |                                     |                                     |
             v                                     v                                     v
+------------------------+             +------------------------+             +------------------------+
|   PostgreSQL 15 DB     |             |      Redis Queue       |             |  Celery Task Worker    |
|   Container: postgres  |             |   Container: redis     |             |  Container: worker     |
|   Port 5432            |             |   Port 6379            |             |  Background ML & Rules |
+------------------------+             +------------------------+             +------------------------+
```

### Steps to Launch
1. **Clone the repository and enter directory**:
   ```bash
   git clone https://github.com/your-org/sentinelai.git
   cd sentinelai
   ```

2. **Configure Environment Variables**:
   Copy `.env.example` to `.env` and review secrets:
   ```bash
   cp .env.example .env
   ```

3. **Build and Run Containers**:
   ```bash
   docker-compose up -d --build
   ```

4. **Verify Container Health**:
   ```bash
   docker-compose ps
   ```

5. **Access Platform**:
   - **SOC Frontend**: `http://localhost` (or `http://localhost:5173` if running dev server)
   - **Backend API**: `http://localhost:8000`
   - **Interactive API Docs**: `http://localhost:8000/docs`

---

## 3. Native Local Lab Setup (Without Docker)

For rapid development and local testing in environments without Docker:

### 3.1 Backend Setup
1. **Navigate to the backend directory and activate a Python virtual environment**:
   ```bash
   cd backend
   python -m venv venv
   # On Windows:
   .\venv\Scripts\Activate.ps1
   # On Linux/macOS:
   source venv/bin/activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Initialize Database and Seed Defaults**:
   ```bash
   alembic upgrade head
   python -c "from app.database.init_db import init_db; from app.database.session import SessionLocal; init_db(SessionLocal())"
   ```

4. **Start the FastAPI server**:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

### 3.2 Frontend Setup
1. **Navigate to the frontend directory**:
   ```bash
   cd ../frontend
   npm install
   ```

2. **Start the Vite development server**:
   ```bash
   npm run dev
   ```
   The UI will be accessible at `http://localhost:5173`.

---

## 4. Default Credentials & Initial Accounts

Upon database initialization, SentinelAI automatically provisions three pre-configured accounts:

| Username | Password | Role | Description |
| :--- | :--- | :--- | :--- |
| **`admin`** | `SentinelAdmin2026!` | `ADMIN` | Platform administrator with rule editing and containment approval permissions. |
| **`analyst`** | `SentinelAnalyst2026!` | `ANALYST` | SOC investigator with incident management and alert triage permissions. |
| **`viewer`** | `SentinelViewer2026!` | `VIEWER` | Read-only executive with access to dashboards and metrics. |

> [!WARNING]
> Change these default passwords immediately upon deployment in production or shared network environments.

---

## 5. Deploying Monitoring Agents

### 5.1 Endpoint Monitoring Agent (Linux / Windows)
1. Copy the `agents/endpoint_agent` directory to the target endpoint.
2. Edit `config.yaml` to specify the SentinelAI backend server URL and API key:
   ```yaml
   backend_url: "http://<sentinelai-server-ip>:8000/api/v1/events/ingest"
   agent_key: "default-sentinel-agent-key"
   host_id: "endpoint-prod-srv-01"
   collection_interval: 10
   ```
3. Run the agent:
   ```bash
   python agent.py
   ```

### 6. Cloud Deployment Guide (Oracle Cloud Always Free & Cloudflare Pages)

### 6.1 Oracle Cloud Always Free VM Setup
1. **Provision an Always Free VM** in the OCI Console:
   - **Image**: Ubuntu 22.04 LTS or 24.04 LTS (Canonical Ubuntu).
   - **Shape**: `VM.Standard.A1.Flex` (Ampere ARM, 2-4 OCPUs, 12-24 GB RAM) or `VM.Standard.E2.1.Micro` (AMD, 1 OCPU, 1 GB RAM).
   - **Networking**: Assign a public IPv4 address and attach an SSH public key.
2. **Configure Security Lists (VCN Firewall)**:
   - Allow Ingress on Port 22 (SSH).
   - Allow Ingress on Port 80 (HTTP / Certbot).
   - Allow Ingress on Port 443 (HTTPS).
3. **SSH into the VM and Install Docker**:
   ```bash
   sudo apt-get update && sudo apt-get install -y docker.io docker-compose-v2 git
   sudo usermod -aG docker ubuntu
   ```
4. **Clone Repository & Launch Services**:
   ```bash
   git clone https://github.com/<your-username>/sentinel-ai.git /opt/sentinelai
   cd /opt/sentinelai
   cp .env.example .env
   # Edit .env with production passwords
   docker compose up -d --build
   ```

### 6.2 Cloudflare Pages Frontend Setup
1. Navigate to **Cloudflare Dashboard $\to$ Workers & Pages $\to$ Create Application $\to$ Pages $\to$ Connect to Git**.
2. Select repository `sentinel-ai`.
3. Configure build settings:
   - **Framework Preset**: `Vite`
   - **Build command**: `npm run build`
   - **Build output directory**: `dist`
   - **Root directory**: `frontend`
4. Configure Environment Variables:
   - `VITE_API_BASE_URL`: `https://api.yourdomain.com/api/v1` (or your OCI VM public IP/domain)
5. Click **Save and Deploy**. Cloudflare automatically provisions a free global SSL certificate and provides the public URL `https://sentinel-ai.pages.dev`.

