from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user, require_roles, log_audit
from app.models.models import ThreatIndicator, User
from app.schemas.schemas import ThreatIndicatorCreate, ThreatIndicatorOut
from app.threat_intelligence.matcher import seed_sample_indicators

router = APIRouter()


@router.get("", response_model=List[ThreatIndicatorOut])
def list_indicators(
    indicator_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Ensure sample indicators exist
    if db.query(ThreatIndicator).count() == 0:
        seed_sample_indicators(db)

    query = db.query(ThreatIndicator)
    if indicator_type:
        query = query.filter(ThreatIndicator.indicator_type == indicator_type.upper())
    if is_active is not None:
        query = query.filter(ThreatIndicator.is_active == is_active)

    return query.order_by(ThreatIndicator.id.desc()).all()


@router.post("/indicators", response_model=ThreatIndicatorOut)
def create_indicator(
    ind_in: ThreatIndicatorCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN", "ANALYST"]))
):
    existing = db.query(ThreatIndicator).filter(ThreatIndicator.value == ind_in.value).first()
    if existing:
        raise HTTPException(status_code=400, detail="Indicator already exists")

    new_ind = ThreatIndicator(
        indicator_type=ind_in.indicator_type.upper(),
        value=ind_in.value,
        threat_type=ind_in.threat_type,
        severity=ind_in.severity.upper(),
        confidence=ind_in.confidence,
        source=ind_in.source,
        is_active=ind_in.is_active,
        expires_at=ind_in.expires_at
    )
    db.add(new_ind)
    db.commit()
    db.refresh(new_ind)

    log_audit(db, "THREAT_INDICATOR_CREATED", current_user.id, "THREAT_INTEL", new_ind.id, {"value": new_ind.value}, request)
    return new_ind


@router.delete("/indicators/{ind_id}")
def delete_indicator(
    ind_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN"]))
):
    ind = db.query(ThreatIndicator).filter(ThreatIndicator.id == ind_id).first()
    if not ind:
        raise HTTPException(status_code=404, detail="Indicator not found")

    ind.is_active = False
    db.commit()
    log_audit(db, "THREAT_INDICATOR_DEACTIVATED", current_user.id, "THREAT_INTEL", ind.id, None, request)
    return {"message": "Indicator deactivated"}
