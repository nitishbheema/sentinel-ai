from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.database.session import engine, Base, SessionLocal
from app.models.models import User, DetectionRule, ThreatIndicator, Endpoint
from app.core.security import get_password_hash
from app.api.v1.api import api_router
from app.detection.engine import rule_engine
from app.threat_intelligence.matcher import seed_sample_indicators

# Create Database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="SentinelAI — Threat Detection & Automated SOC Platform",
    description="Intelligent enterprise cybersecurity monitoring, machine learning intrusion detection, and incident response platform.",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
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
        # 1. Seed Initial Users if not existing
        users_to_seed = [
            ("admin", "admin@sentinelai.local", "SentinelAdmin2026!", "ADMIN"),
            ("analyst", "analyst@sentinelai.local", "SentinelAnalyst2026!", "ANALYST"),
            ("viewer", "viewer@sentinelai.local", "SentinelViewer2026!", "VIEWER"),
        ]
        for uname, uemail, upass, urole in users_to_seed:
            existing = db.query(User).filter(User.username == uname).first()
            if not existing:
                new_user = User(
                    username=uname,
                    email=uemail,
                    hashed_password=get_password_hash(upass),
                    role=urole,
                    is_active=True
                )
                db.add(new_user)
        db.commit()

        # 2. Seed Detection Rules from disk
        rule_engine.sync_rules_to_db(db)

        # 3. Seed Threat Intelligence Indicators
        seed_sample_indicators(db)

        # 4. Seed initial endpoints
        if db.query(Endpoint).count() == 0:
            seed_eps = [
                Endpoint(hostname="sec-lab-srv01", ip_address="192.168.1.10", os_type="linux", os_version="Ubuntu 22.04 LTS", status="ACTIVE", agent_version="1.0.0"),
                Endpoint(hostname="corp-dc-01", ip_address="192.168.1.5", os_type="windows", os_version="Windows Server 2022", status="ACTIVE", agent_version="1.0.0"),
                Endpoint(hostname="fin-ws-analyst", ip_address="192.168.1.104", os_type="linux", os_version="Debian 12", status="ACTIVE", agent_version="1.0.0"),
                Endpoint(hostname="dmz-web-proxy", ip_address="10.0.0.1", os_type="linux", os_version="Alpine Linux 3.19", status="ACTIVE", agent_version="1.0.0")
            ]
            db.add_all(seed_eps)
            db.commit()

        print("[SentinelAI] Startup initialization completed successfully.")
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
