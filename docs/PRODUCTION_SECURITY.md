# SentinelAI Production Security & Hardening Guide

## 1. Executive Summary

SentinelAI provides enterprise-grade cybersecurity monitoring and automated response. Because the platform itself handles sensitive security telemetry and containment controls, production security hardening is paramount.

This document defines the production security controls, network isolation policies, secret management standards, and host hardening procedures implemented for zero-cost cloud deployment.

---

## 2. Network Isolation & Service Perimeter

```
+-------------------------------------------------------------------------------+
|                             PUBLIC INTERNET                                   |
+-------------------------------------------------------------------------------+
           |                                                      |
           | HTTPS (443) / HTTP (80)                              | HTTPS Telemetry
           v                                                      v
+------------------------+                             +------------------------+
|  Cloudflare Pages      |                             |  Nginx Reverse Proxy   |
|  (Frontend CDN)        |                             |  (TLS Termination)     |
+------------------------+                             +-----------+------------+
                                                                   |
+------------------------------------------------------------------|------------+
| ORACLE CLOUD / LINUX VM (DOCKER BRIDGE NETWORKS)                 |            |
|                                                                  v            |
|  +-------------------------------------------------------------------------+  |
|  | SENTINEL_PUBLIC NETWORK                                                 |  |
|  |   [FastAPI Backend Core (Port 8000 Internal)]                           |  |
|  +-------------------------------------+-----------------------------------+  |
|                                        | Internal RPC & Connection Pool       |
|  +-------------------------------------v-----------------------------------+  |
|  | SENTINEL_INTERNAL NETWORK (STRICTLY ISOLATED - NO EXTERNAL ACCESS)      |  |
|  |   [PostgreSQL 15 (Port 5432)]      [Redis 7 (Port 6379 with Password)]  |  |
|  |   [Celery / Worker Queue]          [ML Inference Pipeline]              |  |
|  +-------------------------------------------------------------------------+  |
+-------------------------------------------------------------------------------+
```

### Security Controls Applied:
1. **Zero Public Database Exposure**: PostgreSQL (5432) and Redis (6379) have no mapped host ports in `docker-compose.yml`. They communicate exclusively through Docker's internal bridge network (`sentinel_internal`).
2. **Reverse Proxy TLS Termination**: Only ports 80 and 443 are open to the host. All API requests pass through the Nginx reverse proxy with security headers (`X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: strict-origin-when-cross-origin`).

---

## 3. Authentication & Access Governance

### 3.1 Web User Authentication
- **Password Storage**: Passwords are hashed using the Argon2id algorithm (via Passlib with automatic salt generation), resistant to GPU brute-forcing.
- **Session Tokens**: Dual-token JSON Web Token (JWT) architecture using HMAC-SHA256:
  - **Access Tokens**: Short-lived (60 minutes).
  - **Refresh Tokens**: Long-lived (7 days) with rotation on refresh.
- **Role-Based Access Control (RBAC)**:
  - `ADMIN`: User provisioning, rule editing, response action approvals.
  - `ANALYST`: Incident investigation, alert triage, response action creation.
  - `VIEWER`: Read-only access to dashboards, events, and metrics.

### 3.2 Agent & Sensor Authentication
- Remote endpoint agents authenticate using HMAC-SHA256 signatures (`X-Agent-Signature`) calculated over canonical request payloads.
- Requests include a timestamp (`X-Agent-Timestamp`) validated against a 300-second window to prevent clock skew attacks.
- Nonce replay protection (`X-Agent-Nonce`) tracks unique single-use identifiers to permanently prevent replay attacks.
- All incoming payloads are validated against strict Pydantic schemas. Unrecognized or malformed telemetry is rejected with HTTP 422 before queue processing.

---

## 4. Host OS & Cloud VM Hardening (Ubuntu Linux)

When provisioning the free-tier Linux VM, apply the following baseline hardening:

### 4.1 SSH Configuration (`/etc/ssh/sshd_config`)
```bash
# Disable root login over SSH
PermitRootLogin no

# Enforce public-key authentication only
PasswordAuthentication no
PubkeyAuthentication yes

# Restrict maximum authentication attempts
MaxAuthTries 3
```

### 4.2 Host Firewall (UFW)
```bash
# Set default policies
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow necessary ports
sudo ufw allow 22/tcp   # SSH (or custom port)
sudo ufw allow 80/tcp   # HTTP (Certbot / ACME challenge)
sudo ufw allow 443/tcp  # HTTPS (Reverse Proxy)

# Enable firewall
sudo ufw enable
```

### 4.3 Automated Security Updates
```bash
sudo apt-get install -y unattended-upgrades fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

---

## 5. Non-Destructive Containment Guardrails

In compliance with SOC best practices, SentinelAI enforces analyst authorization for all defensive operations:
- Containment actions (`BLOCK_IP`, `ISOLATE_HOST`) are registered with status `PENDING_APPROVAL`.
- Only users with the `ADMIN` role can execute containment approvals (`POST /api/v1/response/actions/{id}/approve`).
- Every approval, rejection, and rollback operation writes an immutable record to the `audit_logs` table capturing the operator's user ID, IP address, and rationale.
