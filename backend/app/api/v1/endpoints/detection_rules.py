from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user, require_roles, log_audit
from app.models.models import DetectionRule, User
from app.schemas.schemas import DetectionRuleOut, DetectionRuleCreate, DetectionRuleUpdate
from app.detection.engine import rule_engine

router = APIRouter()


@router.get("", response_model=List[DetectionRuleOut])
def list_rules(
    is_enabled: Optional[bool] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Ensure rules are synced to DB
    if db.query(DetectionRule).count() == 0:
        rule_engine.sync_rules_to_db(db)

    query = db.query(DetectionRule)
    if is_enabled is not None:
        query = query.filter(DetectionRule.is_enabled == is_enabled)
    if category:
        query = query.filter(DetectionRule.category == category)

    return query.order_by(DetectionRule.id.asc()).all()


@router.post("", response_model=DetectionRuleOut)
def create_rule(
    rule_in: DetectionRuleCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN"]))
):
    existing = db.query(DetectionRule).filter(DetectionRule.rule_id == rule_in.rule_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Rule with this rule_id already exists")

    new_rule = DetectionRule(
        rule_id=rule_in.rule_id,
        name=rule_in.name,
        description=rule_in.description,
        severity=rule_in.severity.upper(),
        category=rule_in.category,
        condition_yaml=rule_in.condition_yaml,
        is_enabled=rule_in.is_enabled,
        time_window_seconds=rule_in.time_window_seconds,
        threshold=rule_in.threshold,
        mitre_technique_id=rule_in.mitre_technique_id,
        version=rule_in.version
    )
    db.add(new_rule)
    db.commit()
    db.refresh(new_rule)

    log_audit(db, "RULE_CREATED", current_user.id, "RULE", new_rule.id, {"rule_id": new_rule.rule_id}, request)
    return new_rule


@router.patch("/{rule_id}", response_model=DetectionRuleOut)
def update_rule(
    rule_id: int,
    rule_update: DetectionRuleUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN"]))
):
    rule = db.query(DetectionRule).filter(DetectionRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    if rule_update.name is not None:
        rule.name = rule_update.name
    if rule_update.description is not None:
        rule.description = rule_update.description
    if rule_update.severity is not None:
        rule.severity = rule_update.severity.upper()
    if rule_update.condition_yaml is not None:
        rule.condition_yaml = rule_update.condition_yaml
    if rule_update.is_enabled is not None:
        rule.is_enabled = rule_update.is_enabled
    if rule_update.time_window_seconds is not None:
        rule.time_window_seconds = rule_update.time_window_seconds
    if rule_update.threshold is not None:
        rule.threshold = rule_update.threshold
    if rule_update.mitre_technique_id is not None:
        rule.mitre_technique_id = rule_update.mitre_technique_id

    db.commit()
    db.refresh(rule)
    log_audit(db, "RULE_UPDATED", current_user.id, "RULE", rule.id, {"updated_fields": rule_update.dict(exclude_unset=True)}, request)
    return rule
