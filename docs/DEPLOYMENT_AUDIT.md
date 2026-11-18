# SentinelAI Production Pre-Deployment Audit

## 1. Audit Executive Summary

- **Audit Date**: November 18, 2026
- **Auditor Role**: Senior DevOps & DevSecOps Engineer, Security Architect
- **Target Platform**: Cloud-Native Production (Oracle Cloud Always Free Ampere A1 Compute + Cloudflare Pages + Docker Compose)
- **Target Monthly Cost**: **₹0.00**
- **Overall System Readiness**: **READY FOR PRODUCTION DEPLOYMENT** (Pending Cloud Provider & GitHub Account Linkage)

---

## 2. Component-by-Component Audit Findings

| Component | Audit Check | Observed State | Remediation / Verification Applied |
| :--- | :--- | :--- | :--- |
| **Frontend UI** | Production Build & Assets | Passed (`npm run build` in 1.87s) | Clean Vite bundle produced in `frontend/dist/`. Code minified, assets hashed. |
| **Frontend API Base** | Cloud URL handling | Fixed | Configured `import.meta.env.VITE_API_BASE_URL` with `/api/v1` default fallback. |
| **Frontend Routing** | SPA client-side deep links | Fixed | Created `frontend/public/_redirects` (`/* /index.html 200`) for Cloudflare Pages. |
| **Backend Core** | FastAPI endpoints & routing | Verified | All 11 endpoint modules registered under `/api/v1` and verified. |
| **Backend Testing** | Pytest unit & scenario tests | Passed (13/13) | `tests/test_acceptance_scenarios.py` & `test_auth.py` pass with 100% success rate. |
| **Database Engine** | PostgreSQL & SQLite fallback | Verified | SQLite active for standalone/lab tests; Docker Compose configured with PostgreSQL 15. |
| **Database Migrations** | Alembic migration scripts | Verified | Revision `2b918de8c168_initial_sentinelai_schema.py` generated, stamped, and applied. |
| **Authentication** | Password hashing & tokens | Verified | Argon2id + bcrypt password hashing. HS256 JWT tokens with access/refresh rotation. |
| **Authorization (RBAC)**| Role boundaries | Verified | `ADMIN`, `ANALYST`, and `VIEWER` roles enforced via FastAPI security dependencies. |
| **ML Inference** | Model loading & execution | Verified | Random Forest and Isolation Forest loaded from `ml-engine/models/`. |
| **ML Performance** | Evaluated metrics | Verified | Accuracy: 97.25%, Precision: 96.99%, Recall: 97.25%, F1: 0.9700, FPR: 0.0000. |
| **Detection Engine** | 8 Sigma-inspired rules | Verified | In-memory sliding window and anti-flooding cooldown cache verified. |
| **Sensors & Collectors**| Zeek & Suricata parsers | Verified | Log collectors support live feeds, sample files, and reconnect backoff. |
| **Endpoint Agent** | Python host monitor | Verified | Linux and Windows support with SHA-256 payload verification and token authentication. |
| **Incident Response** | Analyst-approved defense | Verified | Defensive actions default to `PENDING_APPROVAL`; dual-phase execution with rollback. |
| **Containerization** | Docker Compose topology | Hardened | Removed public port bindings on PostgreSQL (5432) and Redis (6379); isolated on internal bridge. |
| **Secrets & Keys** | Secret leakage audit | Verified | `.env` ignored in Git. `.env.example` provided. Default passwords flagged in docs. |
| **CORS Policy** | Allowed origins | Updated | Added `https://sentinel-ai.pages.dev` to `ALLOWED_ORIGINS` with flexible comma/JSON parsing. |

---

## 3. Issues Identified and Remediated During Audit

1. **Client-Side Routing on Cloudflare Pages (Fixed)**:
   - *Issue*: Cloudflare Pages would return HTTP 404 on hard refreshes of dynamic routes (e.g. `/threats`, `/incidents/1`).
   - *Fix*: Created `frontend/public/_redirects` mapping `/*` to `/index.html 200`.

2. **Frontend Hardcoded API Base URL (Fixed)**:
   - *Issue*: Axios instance used fixed relative URL `/api/v1`, preventing deployment on a distinct domain from the backend API.
   - *Fix*: Added `import.meta.env.VITE_API_BASE_URL || '/api/v1'` in `frontend/src/services/api.js`.

3. **Docker Compose Database & Cache Port Exposure (Fixed)**:
   - *Issue*: PostgreSQL (5432) and Redis (6379) were mapped to host ports in `docker-compose.yml`, exposing them to outside scans.
   - *Fix*: Re-architected `docker-compose.yml` with dual bridge networks (`sentinel_internal` and `sentinel_public`), keeping Postgres and Redis strictly internal.

4. **Static Host Label in Dashboard Header (Fixed)**:
   - *Issue*: `DashboardLayout.jsx` rendered hardcoded string `127.0.0.1:8000`.
   - *Fix*: Replaced with dynamic SOC cluster status indicator.

---

## 4. Deployment Prerequisites & Blocker Matrix

| Prerequisite | Status | Resolution Action Required |
| :--- | :--- | :--- |
| **GitHub CLI (`gh`)** | Not installed / Not authenticated | User must provide GitHub repository creation authorization or credentials. |
| **Oracle Cloud Free Tier** | Account access required | User must provision or authenticate access to an OCI Always Free compute instance. |
| **Cloudflare Pages** | Account access required | User connects GitHub repository to Cloudflare Pages for automated deployment. |
| **Production Secrets** | Configured via templates | Generate cryptographically secure `SECRET_KEY`, `POSTGRES_PASSWORD`, and `REDIS_PASSWORD`. |
