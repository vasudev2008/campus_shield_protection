from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from ..schemas.models import IncidentCreate, IncidentRead, IncidentUpdate
from ..core.database import get_db
from ..models import Incident, IncidentStatus, IncidentEvent, IncidentEventType, Responder
from ..services.incidents import apply_transition, can_transition
from datetime import datetime

router = APIRouter()

@router.get("/", response_model=List[IncidentRead])
def list_incidents(status: Optional[IncidentStatus] = None, db: Session = Depends(get_db)):
    query = db.query(Incident)
    if status:
        query = query.filter(Incident.status == status)
    return query.all()

@router.post("/", response_model=IncidentRead)
def create_incident(inc: IncidentCreate, db: Session = Depends(get_db)):
    incident = Incident(
        category=inc.category,
        block_id=inc.block_id,
        location_desc=inc.location_desc,
        severity=inc.severity,
        detection_source=inc.detection_source,
        confidence=inc.confidence,
    )
    db.add(incident)
    db.commit()
    db.refresh(incident)
    # Record creation event
    event = IncidentEvent(
        incident_id=incident.id,
        event_type=IncidentEventType.STATE_CHANGE,
        details="Incident created",
        timestamp=datetime.utcnow(),
    )
    db.add(event)
    db.commit()
    return incident

@router.get("/{incident_id}", response_model=IncidentRead)
def get_incident(incident_id: int, db: Session = Depends(get_db)):
    inc = db.query(Incident).filter(Incident.id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")
    return inc

@router.patch("/{incident_id}", response_model=IncidentRead)
def update_incident(
    incident_id: int,
    payload: IncidentUpdate,
    bg: BackgroundTasks,
    db: Session = Depends(get_db),
):
    inc = db.query(Incident).filter(Incident.id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")
    # Handle status transition
    if payload.status:
        try:
            inc = apply_transition(db, inc, payload.status, notes=payload.resolution_notes)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    if payload.assigned_responder_id is not None:
        responder = db.query(Responder).filter(Responder.id == payload.assigned_responder_id).first()
        if not responder:
            raise HTTPException(status_code=404, detail="Responder not found")
        inc.assigned_responder_id = responder.id
        # Record assignment event
        event = IncidentEvent(
            incident_id=inc.id,
            event_type=IncidentEventType.ASSIGNMENT,
            details=f"Assigned to responder {responder.name}",
            timestamp=datetime.utcnow(),
        )
        db.add(event)
    if payload.resolution_notes:
        inc.resolution_notes = payload.resolution_notes
        # Record notes event
        event = IncidentEvent(
            incident_id=inc.id,
            event_type=IncidentEventType.NOTES,
            details=payload.resolution_notes,
            timestamp=datetime.utcnow(),
        )
        db.add(event)
    db.add(inc)
    db.commit()
    db.refresh(inc)
    # Notify UI via internal endpoint (fire‑and‑forget)
    bg.add_task(
        lambda: None  # placeholder for broadcast; real implementation uses internal endpoint
    )
    return inc
