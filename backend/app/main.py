import logging
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.database.session import engine, Base, SessionLocal
from app.models.models import User, DetectionRule, ThreatIndicator, Endpoint
from app.core.security import get_password_hash, validate_password_strength
from app.api.v1.api import api_router
from app.detection.engine import rule_engine
from app.threat_intelligence.matcher import seed_sample_indicators

# Configure logger
logger = logging.getLogger("sentinelai")
logging.basicConfig(level=logging.INFO if not settings.DEBUG else logging.DEBUG)

# Create Database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="SentinelAI — Threat Detection & Automated SOC Platform",
    description="Intelligent enterprise cybersecurity monitoring, machine learning intrusion detection, and incident response platform.",
    version="1.0.0",
    docs_url="/api/docs" if settings.DEBUG or settings.ENVIRONMENT != "production" else None,
    redoc_url="/api/redoc" if settings.DEBUG or settings.ENVIRONMENT != "production" else None,
    openapi_url="/api/openapi.json" if settings.DEBUG or settings.ENVIRONMENT != "production" else None
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    db = SessionLocal()
    try:
        # 1. Check if initial administrator should be bootstrapped from environment
        user_count = db.query(User).count()
        if user_count == 0:
            if settings.INITIAL_ADMIN_USERNAME and settings.INITIAL_ADMIN_PASSWORD:
                is_strong, reason = validate_password_strength(settings.INITIAL_ADMIN_PASSWORD)
                if is_strong:
                    admin_user = User(
                        username=settings.INITIAL_ADMIN_USERNAME.strip(),
                        email=(settings.INITIAL_ADMIN_EMAIL or "admin@sentinelai.local").strip().lower(),
                        hashed_password=get_password_hash(settings.INITIAL_ADMIN_PASSWORD),
                        role="ADMIN",
                        is_active=True
                    )
                    db.add(admin_user)
                    db.commit()
                    logger.info("[SentinelAI] Initial administrator provisioned from environment variables.")
                else:
                    logger.warning(f"[SentinelAI] INITIAL_ADMIN_PASSWORD does not meet complexity requirements: {reason}. Skipping auto-provisioning.")
            else:
                logger.info("[SentinelAI] No initial administrator configured in environment. First-time setup required via UI/API.")

        # 2. Seed Detection Rules from disk
        rule_engine.sync_rules_to_db(db)

        # 3. Seed Threat Intelligence Indicators
        seed_sample_indicators(db)

        # 4. Seed initial endpoints if empty
        if db.query(Endpoint).count() == 0:
            seed_eps = [
                Endpoint(hostname="sec-lab-srv01", ip_address="192.168.1.10", os_type="linux", os_version="Ubuntu 22.04 LTS", status="ACTIVE", agent_version="1.0.0"),
                Endpoint(hostname="corp-dc-01", ip_address="192.168.1.5", os_type="windows", os_version="Windows Server 2022", status="ACTIVE", agent_version="1.0.0"),
                Endpoint(hostname="fin-ws-analyst", ip_address="192.168.1.104", os_type="linux", os_version="Debian 12", status="ACTIVE", agent_version="1.0.0"),
                Endpoint(hostname="dmz-web-proxy", ip_address="10.0.0.1", os_type="linux", os_version="Alpine Linux 3.19", status="ACTIVE", agent_version="1.0.0")
            ]
            db.add_all(seed_eps)
            db.commit()

        logger.info("[SentinelAI] Startup initialization completed successfully.")
    finally:
        db.close()


@app.get("/health", tags=["System"])
@app.get(f"{settings.API_V1_STR}/health", tags=["System"])
def health_check():
    return {
        "status": "healthy",
        "service": "SentinelAI API",
        "version": settings.VERSION,
        "database": "connected",
        "environment": settings.ENVIRONMENT
    }


# Include V1 API Router
app.include_router(api_router, prefix=settings.API_V1_STR)
