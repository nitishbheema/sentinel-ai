# SentinelAI Backup, Recovery & Disaster Management Guide

## 1. Overview & Strategy

Under zero-cost cloud constraints, automated off-site backups ensure platform resiliency against hardware failures, data corruption, or VM recreation.

This guide outlines:
- Automated daily PostgreSQL logical dumps with gzip compression.
- Persistent volume preservation for Docker containers.
- Step-by-step restoration and disaster recovery procedures.

---

## 2. Automated PostgreSQL Backup Script

Create the backup script at `/opt/sentinelai/scripts/backup.sh` on the host:

```bash
#!/bin/bash
set -euo pipefail

# Configuration
BACKUP_DIR="/opt/sentinelai/backups/postgres"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/sentinelai_db_${TIMESTAMP}.sql.gz"
RETENTION_DAYS=7

mkdir -p "${BACKUP_DIR}"

echo "[$(date)] Starting SentinelAI PostgreSQL backup..."

# Dump database through Docker exec
docker exec -t sentinelai_postgres pg_dump -U "${POSTGRES_USER:-sentinel_user}" -d "${POSTGRES_DB:-sentinelai_db}" | gzip > "${BACKUP_FILE}"

echo "[$(date)] Backup completed: ${BACKUP_FILE} ($(du -h "${BACKUP_FILE}" | cut -f1))"

# Prune backups older than retention window
find "${BACKUP_DIR}" -type f -name "sentinelai_db_*.sql.gz" -mtime +${RETENTION_DAYS} -delete
echo "[$(date)] Pruned backups older than ${RETENTION_DAYS} days."
```

### Scheduling via Cron:
```bash
# Add to host crontab (runs daily at 02:00 AM UTC)
0 2 * * * /opt/sentinelai/scripts/backup.sh >> /var/log/sentinelai_backup.log 2>&1
```

---

## 3. Database Restoration Procedure

To restore the SentinelAI database from a compressed backup:

1. **Stop active ingestion services to prevent state divergence**:
   ```bash
   docker compose stop backend worker
   ```

2. **Restore PostgreSQL database from the archive**:
   ```bash
   BACKUP_ARCHIVE="/opt/sentinelai/backups/postgres/sentinelai_db_YYYYMMDD_HHMMSS.sql.gz"
   
   # Decompress and feed into container
   gunzip -c "${BACKUP_ARCHIVE}" | docker exec -i sentinelai_postgres psql -U "${POSTGRES_USER:-sentinel_user}" -d "${POSTGRES_DB:-sentinelai_db}"
   ```

3. **Run database migrations to ensure schema alignment**:
   ```bash
   docker compose run --rm backend alembic upgrade head
   ```

4. **Restart all services**:
   ```bash
   docker compose up -d
   ```

5. **Verify system health**:
   ```bash
   curl -f http://localhost:8000/health
   ```

---

## 4. Disaster Recovery & VM Migration

If migrating to a new free-tier VM or rebuilding after an OS reinstall:
1. Re-clone repository: `git clone https://github.com/your-org/sentinel-ai.git /opt/sentinelai`
2. Restore `.env` file containing original `SECRET_KEY` and credentials.
3. Start base database: `docker compose up -d postgres`
4. Restore most recent backup archive using the restore procedure above.
5. Launch all services: `docker compose up -d --build`
