from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user, require_roles
from app.models.models import AuditLog, User
from app.schemas.schemas import AuditLogOut

router = APIRouter()


@router.get("", response_model=List[AuditLogOut])
def list_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    action: Optional[str] = None,
    target_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN", "ANALYST"]))
):
    query = db.query(AuditLog)
    if action:
        query = query.filter(AuditLog.action == action.upper())
    if target_type:
        query = query.filter(AuditLog.target_type == target_type.upper())

    logs = query.order_by(AuditLog.id.desc()).offset(skip).limit(limit).all()
    results = []
    for log in logs:
        out = AuditLogOut.model_validate(log)
        out.username = log.user.username if log.user else "System"
        results.append(out)
    return results
