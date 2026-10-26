# backend/app/services/alerts.py
"""Alert creation and escalation logic.

The escalation is implemented as a simple ``asyncio`` background task that
waits for the configured timeout (critical or high priority) and, if the
alert has not been acknowledged, creates an escalation record and assigns a
backup responder.

In a production system you would likely use a dedicated task queue (RQ,
Celery, Dramatiq) but for the hack‑athon demo an in‑process coroutine is
sufficient and keeps the code easy to understand.
"""

import asyncio
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from ..models import Alert, Responder, Incident, IncidentStatus, IncidentEvent, IncidentEventType
from ..core.config import settings

# Simple mapping of severity to escalation timeout (seconds)
_ESCALATION_TIMEOUTS = {
    "critical": settings.ALERT_ESCALATION_CRITICAL_SECONDS,
    "high": settings.ALERT_ESCALATION_HIGH_SECONDS,
}

async def _escalate_if_needed(alert_id: int, timeout: int, db_factory):
    """Wait ``timeout`` seconds and, if the alert is still unacknowledged,
    mark it as escalated and assign the backup responder.

    ``db_factory`` is a callable that returns a new ``Session`` – we cannot
    reuse the session that was used when the task was scheduled because the
    original request has already finished.
    """
    await asyncio.sleep(timeout)
    db: Session = db_factory()
    try:
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if not alert or alert.acknowledged_at:
            return  # already handled
        # Mark escalation
        alert.escalated = True
        db.add(alert)
        # Find backup responder for the incident block (role "Backup Responder")
        incident = db.query(Incident).filter(Incident.id == alert.incident_id).first()
        backup = (
            db.query(Responder)
            .filter(
                Responder.block_id == incident.block_id,
                Responder.role == "Backup Responder",
            )
            .first()
        )
        if backup:
            incident.assigned_responder_id = backup.id
            # Record escalation event
            event = IncidentEvent(
                incident_id=incident.id,
                event_type=IncidentEventType.ESCALATION,
                details=f"Escalated to backup responder {backup.name}",
                timestamp=datetime.utcnow(),
            )
            db.add(event)
        db.commit()
    finally:
        db.close()

def schedule_escalation(
    db: Session,
    incident: Incident,
    alert: Alert,
    background_tasks,
    severity: str,
    db_factory,
):
    """Schedule escalation based on severity.

    ``background_tasks`` is the FastAPI ``BackgroundTasks`` instance on which
    we register the coroutine.
    """
    timeout = _ESCALATION_TIMEOUTS.get(severity.lower())
    if timeout is None:
        return  # no escalation for this severity
    background_tasks.add_task(
        _escalation_if_needed,
        alert_id=alert.id,
        timeout=timeout,
        db_factory=db_factory,
    )

def create_alert(db: Session, incident: Incident) -> Alert:
    """Create an ``Alert`` linked to ``incident`` and return it."""
    # Find primary responder for the block (role "Security Officer")
    primary = (
        db.query(Responder)
        .filter(
            Responder.block_id == incident.block_id,
            Responder.role == "Security Officer",
        )
        .first()
    )
    if not primary:
        raise ValueError("No primary responder configured for block")
    alert = Alert(
        incident_id=incident.id,
        responder_id=primary.id,
        created_at=datetime.utcnow(),
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    # Record alert creation event
    event = IncidentEvent(
        incident_id=incident.id,
        event_type=IncidentEventType.STATE_CHANGE,
        details=f"Alert created for responder {primary.name}",
        timestamp=datetime.utcnow(),
    )
    db.add(event)
    db.commit()
    return alert
