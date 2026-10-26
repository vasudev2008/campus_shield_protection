# backend/app/services/incidents.py
"""Incident business logic and state‑transition validation.

The state machine is defined in ``models.IncidentStatus``.  Only the
following transitions are allowed:

* DETECTED -> UNDER_REVIEW
* UNDER_REVIEW -> CONFIRMED or FALSE_ALARM
* CONFIRMED -> DISPATCHED
* DISPATCHED -> RESPONDING
* RESPONDING -> RESOLVED

Any other change results in a ``ValueError`` which is turned into a
``HTTPException`` by the API layer.
"""

from typing import Optional
from sqlalchemy.orm import Session
from ..models import Incident, IncidentStatus, IncidentEvent, IncidentEventType
from datetime import datetime

_allowed_transitions = {
    IncidentStatus.DETECTED: {IncidentStatus.UNDER_REVIEW},
    IncidentStatus.UNDER_REVIEW: {IncidentStatus.CONFIRMED, IncidentStatus.FALSE_ALARM},
    IncidentStatus.CONFIRMED: {IncidentStatus.DISPATCHED},
    IncidentStatus.DISPATCHED: {IncidentStatus.RESPONDING},
    IncidentStatus.RESPONDING: {IncidentStatus.RESOLVED},
    IncidentStatus.RESOLVED: set(),
    IncidentStatus.FALSE_ALARM: set(),
}


def can_transition(current: IncidentStatus, new: IncidentStatus) -> bool:
    """Return ``True`` if ``new`` is a permitted next state.

    The function is deliberately tiny – the heavy lifting (recording the
    transition) is performed by ``apply_transition``.
    """
    return new in _allowed_transitions.get(current, set())


def apply_transition(
    db: Session,
    incident: Incident,
    new_status: IncidentStatus,
    notes: Optional[str] = None,
) -> Incident:
    """Validate and apply a status change.

    A new ``IncidentEvent`` of type ``STATE_CHANGE`` is recorded with a
    human‑readable description.  The incident ``updated_at`` timestamp is
    refreshed.
    """
    if not can_transition(incident.status, new_status):
        raise ValueError(
            f"Invalid transition from {incident.status!s} to {new_status!s}"
        )

    # Record the state‑change event
    event = IncidentEvent(
        incident_id=incident.id,
        event_type=IncidentEventType.STATE_CHANGE,
        details=f"Status changed from {incident.status} to {new_status}" + (
            f" (notes: {notes})" if notes else ""
        ),
        timestamp=datetime.utcnow(),
    )
    incident.status = new_status
    db.add(event)
    db.add(incident)
    db.commit()
    db.refresh(incident)
    return incident
