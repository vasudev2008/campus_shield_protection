# backend/app/api/reports.py
"""Incident Report API endpoints.

Provides filtered incident data for the Incident Reports page, including:
- Summary statistics (total, by severity, by status, by camera)
- Filtered incident records
- Individual incident with full timeline/events
- Average response time calculations from real timestamps
"""

from typing import Optional, List
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..core.database import get_db
from ..models import Incident, IncidentEvent, Responder, CampusBlock
from ..schemas.models import IncidentStatus

router = APIRouter()


@router.get("/summary")
def get_report_summary(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Return summary statistics for the report dashboard.

    All metrics are computed from real DB records, not hardcoded values.
    """
    query = db.query(Incident)

    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date)
            query = query.filter(Incident.detection_timestamp >= start_dt)
        except ValueError:
            pass

    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date)
            query = query.filter(Incident.detection_timestamp <= end_dt)
        except ValueError:
            pass

    incidents = query.all()

    total = len(incidents)

    # By status
    status_counts = {}
    for status in IncidentStatus:
        status_counts[status.value] = sum(1 for i in incidents if i.status == status)

    # By severity (1=low, 2=medium, 3=high, 4=critical, 5=critical)
    severity_map = {1: "low", 2: "medium", 3: "high", 4: "critical", 5: "critical"}
    severity_counts = {"low": 0, "medium": 0, "high": 0, "critical": 0}
    for i in incidents:
        label = severity_map.get(i.severity, "medium")
        severity_counts[label] += 1

    # By detection source
    source_counts = {}
    for i in incidents:
        src = i.detection_source or "UNKNOWN"
        source_counts[src] = source_counts.get(src, 0) + 1

    # By camera (using location_desc as proxy - no camera_id in DB model)
    location_counts = {}
    for i in incidents:
        loc = i.location_desc or "Unknown"
        location_counts[loc] = location_counts.get(loc, 0) + 1

    # Average response time (DETECTED -> RESOLVED, based on event timestamps)
    response_times = []
    for inc in incidents:
        if inc.status == IncidentStatus.RESOLVED:
            # Get first DETECTED event and RESOLVED event timestamps
            events = (
                db.query(IncidentEvent)
                .filter(IncidentEvent.incident_id == inc.id)
                .order_by(IncidentEvent.timestamp)
                .all()
            )
            detected_at = inc.detection_timestamp
            resolved_event = next(
                (e for e in reversed(events) if "resolved" in (e.details or "").lower()),
                None,
            )
            if resolved_event and detected_at:
                delta = (resolved_event.timestamp - detected_at).total_seconds() / 60
                if delta > 0:
                    response_times.append(delta)

    avg_response_min = (
        round(sum(response_times) / len(response_times), 1) if response_times else None
    )

    # 7-day trend
    trend = []
    now = datetime.utcnow()
    for d in range(6, -1, -1):
        day = now - timedelta(days=d)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        count = sum(
            1
            for i in incidents
            if day_start <= i.detection_timestamp < day_end
        )
        trend.append({"date": day_start.strftime("%b %d"), "count": count})

    return {
        "total": total,
        "by_status": status_counts,
        "by_severity": severity_counts,
        "by_source": source_counts,
        "by_location": location_counts,
        "avg_response_minutes": avg_response_min,
        "trend": trend,
        "date_range": {
            "start": start_date,
            "end": end_date,
        },
    }


@router.get("/incidents")
def list_report_incidents(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    status: Optional[str] = None,
    severity: Optional[str] = None,
    detection_source: Optional[str] = None,
    location: Optional[str] = None,
    category: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """Return filtered incident records for the report table."""
    query = db.query(Incident)

    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date)
            query = query.filter(Incident.detection_timestamp >= start_dt)
        except ValueError:
            pass

    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date)
            query = query.filter(Incident.detection_timestamp <= end_dt)
        except ValueError:
            pass

    if status:
        query = query.filter(Incident.status == status)

    if detection_source:
        query = query.filter(Incident.detection_source == detection_source)

    if location:
        query = query.filter(Incident.location_desc.ilike(f"%{location}%"))

    if category:
        query = query.filter(Incident.category.ilike(f"%{category}%"))

    if severity:
        severity_map = {"low": [1], "medium": [2], "high": [3], "critical": [4, 5]}
        sev_vals = severity_map.get(severity.lower(), [])
        if sev_vals:
            query = query.filter(Incident.severity.in_(sev_vals))

    total_count = query.count()
    incidents = (
        query.order_by(Incident.detection_timestamp.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    result = []
    for inc in incidents:
        # Get responder name
        responder_name = None
        if inc.assigned_responder_id:
            resp = db.query(Responder).filter(Responder.id == inc.assigned_responder_id).first()
            responder_name = resp.name if resp else None

        # Get block name
        block_name = None
        if inc.block_id:
            block = db.query(CampusBlock).filter(CampusBlock.id == inc.block_id).first()
            block_name = block.name if block else None

        # Severity label
        severity_labels = {1: "Low", 2: "Medium", 3: "High", 4: "Critical", 5: "Critical"}
        severity_label = severity_labels.get(inc.severity, "Medium")

        result.append({
            "id": inc.id,
            "category": inc.category,
            "block_id": inc.block_id,
            "block_name": block_name,
            "location_desc": inc.location_desc,
            "severity": inc.severity,
            "severity_label": severity_label,
            "detection_timestamp": inc.detection_timestamp.isoformat() if inc.detection_timestamp else None,
            "detection_source": inc.detection_source,
            "confidence": inc.confidence,
            "assigned_responder_id": inc.assigned_responder_id,
            "assigned_responder_name": responder_name,
            "status": inc.status.value if inc.status else None,
            "resolution_notes": inc.resolution_notes,
            "created_at": inc.created_at.isoformat() if inc.created_at else None,
            "updated_at": inc.updated_at.isoformat() if inc.updated_at else None,
        })

    return {"total": total_count, "incidents": result, "skip": skip, "limit": limit}


@router.get("/incidents/{incident_id}/detail")
def get_incident_detail(incident_id: int, db: Session = Depends(get_db)):
    """Return full incident detail with timeline events."""
    inc = db.query(Incident).filter(Incident.id == incident_id).first()
    if not inc:
        return {"error": "Incident not found"}

    # Get all events/timeline
    events = (
        db.query(IncidentEvent)
        .filter(IncidentEvent.incident_id == inc.id)
        .order_by(IncidentEvent.timestamp)
        .all()
    )

    timeline = [
        {
            "id": e.id,
            "event_type": e.event_type.value if e.event_type else None,
            "timestamp": e.timestamp.isoformat() if e.timestamp else None,
            "details": e.details,
        }
        for e in events
    ]

    # Get responder
    responder_name = None
    if inc.assigned_responder_id:
        resp = db.query(Responder).filter(Responder.id == inc.assigned_responder_id).first()
        responder_name = resp.name if resp else None

    # Get block
    block_name = None
    if inc.block_id:
        block = db.query(CampusBlock).filter(CampusBlock.id == inc.block_id).first()
        block_name = block.name if block else None

    severity_labels = {1: "Low", 2: "Medium", 3: "High", 4: "Critical", 5: "Critical"}

    return {
        "id": inc.id,
        "category": inc.category,
        "block_id": inc.block_id,
        "block_name": block_name,
        "location_desc": inc.location_desc,
        "severity": inc.severity,
        "severity_label": severity_labels.get(inc.severity, "Medium"),
        "detection_timestamp": inc.detection_timestamp.isoformat() if inc.detection_timestamp else None,
        "detection_source": inc.detection_source,
        "confidence": inc.confidence,
        "assigned_responder_id": inc.assigned_responder_id,
        "assigned_responder_name": responder_name,
        "status": inc.status.value if inc.status else None,
        "resolution_notes": inc.resolution_notes,
        "created_at": inc.created_at.isoformat() if inc.created_at else None,
        "updated_at": inc.updated_at.isoformat() if inc.updated_at else None,
        "timeline": timeline,
    }
