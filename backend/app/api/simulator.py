# backend/app/api/simulator.py
"""Demo scenario execution API.

Provides three endpoints to trigger the hackathon‑style simulation scenarios:

* **Scenario A** – successful end‑to‑end response (detect → confirm → dispatch →
  respond → resolve).
* **Scenario B** – escalation demo (critical incident that is not
  acknowledged, causing automatic escalation to backup responder).
* **Scenario C** – false‑alarm workflow.

A ``/reset`` endpoint clears all demo data and reseeds the database.
"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from ..core.database import get_db, SessionLocal
from ..models import (
    Incident,
    IncidentStatus,
    Responder,
    Alert,
    CampusBlock,
)
from ..schemas.models import IncidentRead, AlertRead
from ..services.incidents import apply_transition
from ..services.alerts import create_alert, schedule_escalation
from ..services.seed import seed_demo_data

router = APIRouter()

def _first_block(db: Session) -> CampusBlock:
    """Return the first campus block – used for demo scenarios.
    The ``seed_demo_data`` function ensures at least one block exists.
    """
    block = db.query(CampusBlock).first()
    if not block:
        raise HTTPException(status_code=500, detail="No campus blocks seeded")
    return block

@router.post("/scenario/{name}", response_model=dict)
def run_scenario(
    name: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    name = name.lower()
    if name not in {"a", "b", "c"}:
        raise HTTPException(status_code=400, detail="Invalid scenario name (a, b, c)")

    block = _first_block(db)

    # Common incident attributes
    incident = Incident(
        category="Fall" if name == "a" else "Fire" if name == "b" else "Unknown",
        block_id=block.id,
        location_desc=f"Demo location in {block.name}",
        severity=2 if name == "a" else 5 if name == "b" else 1,
        detection_source="SIMULATED",
        confidence=None,
    )
    db.add(incident)
    db.commit()
    db.refresh(incident)

    # Scenario A – full successful flow
    if name == "a":
        # Create alert and immediately acknowledge it
        alert = create_alert(db, incident)
        alert.acknowledged_at = datetime.utcnow()
        db.add(alert)
        db.commit()
        # Progress incident through all states
        for next_state in [
            IncidentStatus.UNDER_REVIEW,
            IncidentStatus.CONFIRMED,
            IncidentStatus.DISPATCHED,
            IncidentStatus.RESPONDING,
            IncidentStatus.RESOLVED,
        ]:
            apply_transition(db, incident, next_state)
        db.commit()
        return {"scenario": "a", "incident_id": incident.id}

    # Scenario B – escalation (critical incident, no early ack)
    if name == "b":
        alert = create_alert(db, incident)
        # Use a short timeout (5 seconds) for demonstration purposes
        db_factory = lambda: SessionLocal()
        schedule_escalation(db, incident, alert, background_tasks, "critical", db_factory)
        # Advance incident to CONFIRMED so the alert is active
        apply_transition(db, incident, IncidentStatus.UNDER_REVIEW)
        apply_transition(db, incident, IncidentStatus.CONFIRMED)
        db.commit()
        return {"scenario": "b", "incident_id": incident.id, "alert_id": alert.id}

    # Scenario C – false alarm
    if name == "c":
        apply_transition(db, incident, IncidentStatus.UNDER_REVIEW)
        apply_transition(db, incident, IncidentStatus.FALSE_ALARM)
        db.commit()
        return {"scenario": "c", "incident_id": incident.id}

    # Unreachable – kept for type‑checkers
    raise HTTPException(status_code=400, detail="Unhandled scenario")

@router.post("/reset", response_model=dict)
def reset_demo(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    # Truncate all demo tables (order respects FK constraints)
    for table in ["alerts", "incidents", "incident_events", "cameras", "responders", "campus_blocks", "users"]:
        db.execute(f"DELETE FROM {table}")
    db.commit()
    # Reseed asynchronously so the request returns quickly
    background_tasks.add_task(seed_demo_data, db)
    return {"detail": "Demo data reset and reseeded"}
