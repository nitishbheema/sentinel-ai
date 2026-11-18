from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth,
    events,
    alerts,
    incidents,
    analytics,
    ml,
    threat_intelligence,
    response,
    audit,
    detection_rules,
    endpoints
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication & Users"])
api_router.include_router(events.router, prefix="/events", tags=["Event Ingestion & Query"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["Security Alerts"])
api_router.include_router(incidents.router, prefix="/incidents", tags=["Incident Management"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["SOC Analytics"])
api_router.include_router(ml.router, prefix="/ml", tags=["Machine Learning"])
api_router.include_router(threat_intelligence.router, prefix="/threat-intelligence", tags=["Threat Intelligence"])
api_router.include_router(response.router, prefix="/response", tags=["Defensive Response"])
api_router.include_router(audit.router, prefix="/audit-logs", tags=["Audit Logging"])
api_router.include_router(detection_rules.router, prefix="/detection-rules", tags=["Detection Rules"])
api_router.include_router(endpoints.router, prefix="/endpoints", tags=["Endpoint Telemetry"])
