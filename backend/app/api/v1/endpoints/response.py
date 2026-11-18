from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user, require_roles, log_audit
from app.models.models import ResponseAction, Endpoint, User
from app.schemas.schemas import ResponseActionOut, ResponseActionApproval

router = APIRouter()


@router.get("/actions", response_model=List[ResponseActionOut])
def list_response_actions(
    status: Optional[str] = None,
    action_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(ResponseAction)
    if status:
        query = query.filter(ResponseAction.status == status.upper())
    if action_type:
        query = query.filter(ResponseAction.action_type == action_type.upper())

    return query.order_by(ResponseAction.id.desc()).all()


@router.post("/{action_id}/approve", response_model=ResponseActionOut)
def approve_response_action(
    action_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN", "ANALYST"]))
):
    act = db.query(ResponseAction).filter(ResponseAction.id == action_id).first()
    if not act:
        raise HTTPException(status_code=404, detail="Response action not found")

    if act.status not in ["PENDING_APPROVAL"]:
        raise HTTPException(status_code=400, detail=f"Action is already {act.status}")

    # Analyst-approved defensive execution simulation
    now = datetime.now(timezone.utc)
    act.status = "EXECUTED"
    act.approved_by_user_id = current_user.id
    act.updated_at = now

    sim_details = {
        "execution_timestamp": now.isoformat(),
        "executor": current_user.username,
        "action": act.action_type,
        "target": act.target,
        "lab_enforcement": "SIMULATED_CONTAINMENT_SUCCESS",
        "command_dispatched": f"iptables -A INPUT -s {act.target} -j DROP" if act.action_type == "BLOCK_IP" else f"sentinel-agent --isolate --host {act.target}"
    }

    # If action is ISOLATE_HOST, mark endpoint isolated
    if act.action_type == "ISOLATE_HOST":
        ep = db.query(Endpoint).filter(Endpoint.hostname == act.target).first()
        if ep:
            ep.isolation_status = True
            ep.status = "ISOLATED"

    act.execution_result = sim_details
    db.commit()
    db.refresh(act)

    log_audit(db, "RESPONSE_ACTION_APPROVED", current_user.id, "RESPONSE_ACTION", act.id, sim_details, request)
    return act


@router.post("/{action_id}/reject", response_model=ResponseActionOut)
def reject_response_action(
    action_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN", "ANALYST"]))
):
    act = db.query(ResponseAction).filter(ResponseAction.id == action_id).first()
    if not act:
        raise HTTPException(status_code=404, detail="Response action not found")

    act.status = "REJECTED"
    act.approved_by_user_id = current_user.id
    act.updated_at = datetime.now(timezone.utc)
    act.execution_result = {"rejected_by": current_user.username, "reason": "Analyst determined action unwarranted"}
    db.commit()
    db.refresh(act)

    log_audit(db, "RESPONSE_ACTION_REJECTED", current_user.id, "RESPONSE_ACTION", act.id, act.execution_result, request)
    return act


@router.post("/{action_id}/rollback", response_model=ResponseActionOut)
def rollback_response_action(
    action_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN", "ANALYST"]))
):
    act = db.query(ResponseAction).filter(ResponseAction.id == action_id).first()
    if not act:
        raise HTTPException(status_code=404, detail="Response action not found")

    if act.status != "EXECUTED":
        raise HTTPException(status_code=400, detail="Only executed actions can be rolled back")

    act.status = "ROLLED_BACK"
    now = datetime.now(timezone.utc)
    act.updated_at = now

    rollback_details = {
        "rollback_timestamp": now.isoformat(),
        "rolled_back_by": current_user.username,
        "status": "CONTAINMENT_LIFTED",
        "command_dispatched": f"iptables -D INPUT -s {act.target} -j DROP" if act.action_type == "BLOCK_IP" else f"sentinel-agent --un-isolate --host {act.target}"
    }

    if act.action_type == "ISOLATE_HOST":
        ep = db.query(Endpoint).filter(Endpoint.hostname == act.target).first()
        if ep:
            ep.isolation_status = False
            ep.status = "ACTIVE"

    act.execution_result = rollback_details
    db.commit()
    db.refresh(act)

    log_audit(db, "RESPONSE_ACTION_ROLLED_BACK", current_user.id, "RESPONSE_ACTION", act.id, rollback_details, request)
    return act
