# SentinelAI Cloud Architecture & Zero-Cost Infrastructure Design

## 1. High-Level Cloud Topology

SentinelAI is engineered for a cloud-only topology targeting **₹0.00/month** operational cost using perpetual free-tier allocations:

```
[ Remote Endpoint Agents / Sensors ]        [ SOC Analysts & Browser Clients ]
               |                                           |
               | HTTPS Telemetry (Port 443)                | HTTPS UI (Port 443)
               v                                           v
+-------------------------------+           +-------------------------------+
|  Cloudflare Edge / Free DNS   |           |  Cloudflare Pages (Global CDN)|
|  - DDoS Protection            |           |  - React 18 SPA Delivery      |
|  - Free SSL / TLS Termination |           |  - Client-side Routing        |
+---------------+---------------+           +---------------+---------------+
                |                                           |
                | Forward to Public IPv4                    | REST API Calls (CORS)
                v                                           v
+---------------------------------------------------------------------------+
| ORACLE CLOUD INFRASTRUCTURE (ALWAYS FREE ELIGIBLE ARM/AMD INSTANCE)       |
| OS: Ubuntu 22.04 LTS / 24.04 LTS                                          |
|                                                                           |
|   +-------------------------------------------------------------------+   |
|   | NGINX REVERSE PROXY CONTAINER (Ports 80 / 443)                    |   |
|   | - Let's Encrypt / Certbot SSL Auto-Renewal                        |   |
|   | - Rate Limiting & Threat Header Inspection                        |   |
|   +---------------------------------+---------------------------------+   |
|                                     |                                     |
|                                     v                                     |
|   +-------------------------------------------------------------------+   |
|   | FASTAPI APPLICATION CONTAINER (Port 8000 Internal)                |   |
|   | - Event Ingestion, Normalization & Hash Deduplication             |   |
|   | - Sigma Detection Rules Engine (8 Rules)                          |   |
|   | - Scikit-learn ML Inference (Random Forest + Isolation Forest)    |   |
|   | - Multi-Stage Temporal Attack Correlator                          |   |
|   | - 0-100 Composite Risk Scoring Engine                             |   |
|   +-------------------+-----------------------------+-----------------+   |
|                       |                             |                     |
|                       v                             v                     |
|   +-----------------------+     +-----------------------+                 |
|   | POSTGRESQL 15 DB      |     | REDIS 7 IN-MEMORY     |                 |
|   | - 13 Relational Tables|     | - Task Queue / Cache  |                 |
|   | - JSONB Metadata      |     | - Worker Messaging    |                 |
|   | - Persistent Volume   |     | - Internal Only       |                 |
|   +-----------------------+     +-----------------------+                 |
+---------------------------------------------------------------------------+
```

---

## 2. Cloud Resource Allocation & Free-Tier Eligibility

| Provider | Service / Tier | Capacity Utilized | Monthly Cost | Eligibility Status |
| :--- | :--- | :--- | :--- | :--- |
| **Oracle Cloud (OCI)** | Always Free Ampere A1 (ARM64) or E2.1.Micro (x86_64) | 2–4 OCPU, 12–24 GB RAM, 50–200 GB Block Volume, 1 Public IPv4 | **₹0.00** | Always Free (Perpetual, No Trial Expiry) |
| **Cloudflare** | Cloudflare Pages (Free Plan) | Unlimited requests, 500 builds/mo, Global CDN, SSL | **₹0.00** | Always Free |
| **Let's Encrypt** | Automated ACME TLS Certificates | Domain validation, 90-day auto-renewing certs | **₹0.00** | Free / Non-profit |
| **GitHub** | GitHub Free | Public repositories, GitHub Actions (2,000 CI mins/mo) | **₹0.00** | Free |
| **Total Projected Monthly Cost** | | | **₹0.00** | Guaranteed Permanent Free Tier |

---

## 3. Alternative Cloud Deployments (If OCI Capacity Is Saturated)

If Oracle Cloud Ampere A1 capacity is temporarily unavailable in a given geographic region, the following genuine zero-cost configurations can be deployed seamlessly using the existing Docker Compose specifications:

1. **Google Cloud Platform (GCP) Always Free Tier**:
   - `e2-micro` instance (2 vCPUs, 1 GB RAM, 30 GB standard persistent disk) in `us-central1`, `us-east1`, or `us-west1`.
   - *Optimization*: Run lightweight SQLite mode (`DATABASE_URL=sqlite:///./sentinelai.db`) and in-process event queues to operate comfortably within 1 GB RAM.
2. **Koyeb / Render Free Tiers**:
   - Web service deployment running FastAPI backend with attached PostgreSQL free tier.
3. **Fly.io**:
   - Up to 3 shared-cpu-1x 256MB VMs within free allowances.
