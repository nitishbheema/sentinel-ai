# SentinelAI CI/CD Automation & Deployment Pipeline

## 1. Overview

SentinelAI employs an automated continuous integration and continuous deployment (CI/CD) architecture powered by GitHub Actions.

- **CI Pipeline (`.github/workflows/ci.yml`)**: Executes on every pull request and push to `main`/`master`, performing automated testing, linting, frontend builds, and Docker packaging validation.
- **CD Pipeline (`.github/workflows/cd.yml`)**: Triggers on version tag releases (`v*`) or manual execution (`workflow_dispatch`), deploying the frontend to Cloudflare Pages and updating backend services on the Oracle Cloud VM.

---

## 2. CI Pipeline Stages

```
[ Push / PR Event ]
        |
        +-----------------------+-----------------------+
        |                       |                       |
        v                       v                       v
[ Frontend Checks ]     [ Backend Checks ]      [ Docker Builds ]
- Node.js 20 Setup      - Python 3.10 Setup     - Buildx Setup
- Dependency `npm ci`   - Dependency `pip`      - Backend Dockerfile
- `npm run build`       - Pytest Suite (13/13)  - Frontend Dockerfile
- Syntax validation     - Scenarios 1-10 check  - Cache verification
```

---

## 3. CD Pipeline & Deployment Secrets

To enable automated CD deployment, configure the following secrets under **GitHub Repository Settings $\to$ Secrets and variables $\to$ Actions**:

| Secret Name | Purpose | Example Value |
| :--- | :--- | :--- |
| `CLOUDFLARE_API_TOKEN` | Deploys static build to Cloudflare Pages | `cf_token_abcdef123456...` |
| `CLOUDFLARE_ACCOUNT_ID` | Cloudflare account identifier | `9a8b7c6d5e4f3a2b1c...` |
| `PROD_API_BASE_URL` | Public production backend API URL | `https://api.sentinelai.yourdomain.com/api/v1` |
| `OCI_VM_HOST` | Public IPv4 address of the Oracle Cloud VM | `140.238.xxx.xxx` |
| `OCI_VM_USER` | SSH username on the VM | `ubuntu` |
| `OCI_SSH_KEY` | Private SSH key authorized in `~/.ssh/authorized_keys` | `-----BEGIN OPENSSH PRIVATE KEY-----...` |

---

## 4. Safe Deployment Rollback

If a production update introduces issues:
1. Revert to the prior Git tag release:
   ```bash
   git checkout tags/v1.0.0
   ```
2. Trigger the CD workflow on the previous tag, or execute recovery directly on the cloud VM:
   ```bash
   cd /opt/sentinelai
   git checkout tags/v1.0.0
   docker compose up -d --build
   ```
