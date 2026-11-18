from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user, require_roles, log_audit
from app.models.models import Incident, IncidentNote, IncidentEvent, User
from app.schemas.schemas import (
    IncidentCreate,
    IncidentUpdate,
    IncidentOut,
    IncidentNoteCreate,
    IncidentNoteOut
)

router = APIRouter()


@router.get("", response_model=List[IncidentOut])
def list_incidents(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    severity: Optional[str] = None,
    status: Optional[str] = None,
    assigned_to: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Incident)
    if severity:
        query = query.filter(Incident.severity == severity.upper())
    if status:
        query = query.filter(Incident.status == status.upper())
    if assigned_to:
        query = query.filter(Incident.assigned_to_user_id == assigned_to)

    incidents = query.order_by(Incident.id.desc()).offset(skip).limit(limit).all()
    results = []
    for inc in incidents:
        out = IncidentOut.model_validate(inc)
        out.assigned_to_username = inc.assigned_to.username if inc.assigned_to else None
        out.events_count = len(inc.events)
        out.notes = [
            IncidentNoteOut(
                id=n.id,
                incident_id=n.incident_id,
                user_id=n.user_id,
                author_username=n.author.username if n.author else "System",
                note=n.note,
                created_at=n.created_at
            ) for n in inc.notes
        ]
        results.append(out)
    return results


@router.post("", response_model=IncidentOut)
def create_incident(
    inc_in: IncidentCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN", "ANALYST"]))
):
    new_inc = Incident(
        title=inc_in.title,
        description=inc_in.description,
        severity=inc_in.severity.upper(),
        status=inc_in.status.upper(),
        assigned_to_user_id=inc_in.assigned_to_user_id or current_user.id,
        risk_score=inc_in.risk_score,
        mitre_tactics=inc_in.mitre_tactics or []
    )
    db.add(new_inc)
    db.commit()
    db.refresh(new_inc)

    if inc_in.event_ids:
        for eid in inc_in.event_ids:
            db.add(IncidentEvent(incident_id=new_inc.id, event_id=eid))
        db.commit()

    log_audit(db, "INCIDENT_CREATED", current_user.id, "INCIDENT", new_inc.id, {"title": new_inc.title, "severity": new_inc.severity}, request)

    out = IncidentOut.model_validate(new_inc)
    out.assigned_to_username = current_user.username
    out.events_count = len(inc_in.event_ids or [])
    out.notes = []
    return out


@router.get("/{incident_id}", response_model=IncidentOut)
def get_incident(
    incident_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    inc = db.query(Incident).filter(Incident.id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")

    out = IncidentOut.model_validate(inc)
    out.assigned_to_username = inc.assigned_to.username if inc.assigned_to else None
    out.events_count = len(inc.events)
    out.notes = [
        IncidentNoteOut(
            id=n.id,
            incident_id=n.incident_id,
            user_id=n.user_id,
            author_username=n.author.username if n.author else "System",
            note=n.note,
            created_at=n.created_at
        ) for n in inc.notes
    ]
    return out


@router.patch("/{incident_id}", response_model=IncidentOut)
def update_incident(
    incident_id: int,
    inc_update: IncidentUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN", "ANALYST"]))
):
    inc = db.query(Incident).filter(Incident.id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")

    if inc_update.title:
        inc.title = inc_update.title
    if inc_update.description:
        inc.description = inc_update.description
    if inc_update.severity:
        inc.severity = inc_update.severity.upper()
    if inc_update.status:
        inc.status = inc_update.status.upper()
    if inc_update.assigned_to_user_id is not None:
        inc.assigned_to_user_id = inc_update.assigned_to_user_id
    if inc_update.risk_score is not None:
        inc.risk_score = inc_update.risk_score

    db.commit()
    db.refresh(inc)
    log_audit(db, "INCIDENT_UPDATED", current_user.id, "INCIDENT", inc.id, {"status": inc.status, "severity": inc.severity}, request)

    out = IncidentOut.model_validate(inc)
    out.assigned_to_username = inc.assigned_to.username if inc.assigned_to else None
    out.events_count = len(inc.events)
    return out


@router.post("/{incident_id}/notes", response_model=IncidentNoteOut)
def add_incident_note(
    incident_id: int,
    note_in: IncidentNoteCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN", "ANALYST"]))
):
    inc = db.query(Incident).filter(Incident.id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")

    note = IncidentNote(
        incident_id=incident_id,
        user_id=current_user.id,
        note=note_in.note
    )
    db.add(note)
    db.commit()
    db.refresh(note)

    log_audit(db, "INCIDENT_NOTE_ADDED", current_user.id, "INCIDENT", incident_id, {"note_id": note.id}, request)

    return IncidentNoteOut(
        id=note.id,
        incident_id=note.incident_id,
        user_id=note.user_id,
        author_username=current_user.username,
        note=note.note,
        created_at=note.created_at
    )
