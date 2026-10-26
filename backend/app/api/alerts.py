from typing import List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from ..schemas.models import AlertRead, IncidentRead
from ..core.database import get_db, SessionLocal
from ..models import Alert, Incident, IncidentStatus, Responder
from ..services.alerts import create_alert, schedule_escalation

router = APIRouter()

@router.get("/", response_model=List[AlertRead])
def list_alerts(db: Session = Depends(get_db)):
    return db.query(Alert).all()

@router.post("/incident/{incident_id}", response_model=AlertRead)
def trigger_alert(
    incident_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    if incident.status != IncidentStatus.CONFIRMED:
        raise HTTPException(status_code=400, detail="Alert can only be created for confirmed incidents")
    # Create alert and assign primary responder
    try:
        alert = create_alert(db, incident)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    # Schedule escalation based on severity
    severity_label = "critical" if incident.severity >= 4 else "high" if incident.severity >= 3 else None
    if severity_label:
        # Provide a factory to obtain fresh sessions inside the background task
        db_factory = lambda: SessionLocal()
        schedule_escalation(db, incident, alert, background_tasks, severity_label, db_factory)
    return alert

@router.patch("/{alert_id}", response_model=AlertRead)
def acknowledge_alert(
    alert_id: int,
    db: Session = Depends(get_db),
):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    if alert.acknowledged_at:
        raise HTTPException(status_code=400, detail="Alert already acknowledged")
    alert.acknowledged_at = datetime.utcnow()
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert

from datetime import datetime
