from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import datetime
import random

app = FastAPI(title="Smart Campus Shield API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for serverless demo
class Incident(BaseModel):
    id: str
    event_type: str
    camera_id: str
    location: str
    confidence: float
    timestamp: str
    status: str
    source: str
    description: str

class Camera(BaseModel):
    id: str
    name: str
    location: str
    status: str
    detectionActive: bool

class CampusBlock(BaseModel):
    id: int
    name: str
    description: str

CAMPUS_BLOCKS = [
    {"id": 1, "name": "Block A", "description": "Engineering block"},
    {"id": 2, "name": "Block B", "description": "Science block"},
    {"id": 3, "name": "Library", "description": "Main library"},
    {"id": 4, "name": "Laboratory", "description": "Research labs"},
    {"id": 5, "name": "Cafeteria", "description": "Food services"},
    {"id": 6, "name": "Hostel", "description": "Student residence"},
    {"id": 7, "name": "Main Gate", "description": "Entrance"},
]

CAMERAS = [
    {"id": "CAM-01", "name": "Camera 01", "location": "Block A - Ground Floor", "status": "ONLINE", "detectionActive": True},
    {"id": "CAM-02", "name": "Camera 02", "location": "Block B - Corridor", "status": "ONLINE", "detectionActive": True},
    {"id": "CAM-03", "name": "Camera 03", "location": "Main Gate", "status": "ONLINE", "detectionActive": True},
    {"id": "CAM-04", "name": "Camera 04", "location": "Canteen", "status": "ONLINE", "detectionActive": True},
]

INCIDENTS = [
    {
        "id": "INC-INIT-01",
        "event_type": "PERSON_FALL",
        "camera_id": "CAM-01",
        "location": "Block A - Ground Floor",
        "confidence": 94.2,
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "status": "ACTIVE",
        "source": "AI_MODEL",
        "description": "Person fall detected with high confidence at Block A entrance."
    },
    {
        "id": "INC-INIT-02",
        "event_type": "SMOKE_FIRE",
        "camera_id": "CAM-04",
        "location": "Cafeteria",
        "confidence": 88.5,
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "status": "RESOLVED",
        "source": "AI_MODEL",
        "description": "Minor thermal spike resolved by cafeteria staff."
    }
]

@app.get("/api/health/ping")
def ping():
    return {"status": "ok", "service": "Smart Campus Shield API", "timestamp": datetime.datetime.utcnow().isoformat()}

@app.get("/api/blocks")
def get_blocks():
    return CAMPUS_BLOCKS

@app.get("/api/cameras")
def get_cameras():
    return CAMERAS

@app.get("/api/incidents")
def get_incidents():
    return INCIDENTS

@app.get("/api/reports/summary")
def get_reports_summary(start_date: Optional[str] = None, end_date: Optional[str] = None):
    total = len(INCIDENTS)
    by_status = {"ACTIVE": 0, "ACKNOWLEDGED": 0, "RESOLVED": 0, "FALSE_ALARM": 0, "UNDER_REVIEW": 0}
    by_severity = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
    by_source = {"AI": 0, "DEMO": 0, "MANUAL": 0}
    by_location = {}

    for inc in INCIDENTS:
        st = inc.get("status", "ACTIVE")
        by_status[st] = by_status.get(st, 0) + 1
        src = inc.get("source", "DEMO")
        by_source[src] = by_source.get(src, 0) + 1
        loc = inc.get("location", "Unknown")
        by_location[loc] = by_location.get(loc, 0) + 1
        ev_type = inc.get("event_type", "")
        if ev_type in ["FIGHT", "SMOKE_FIRE"]:
            by_severity["Critical"] += 1
        elif ev_type in ["RESTRICTED_ZONE", "PERSON_FALL"]:
            by_severity["High"] += 1
        elif ev_type in ["ASSISTANCE_REQUIRED", "SAFETY_HAZARD"]:
            by_severity["Medium"] += 1
        else:
            by_severity["Low"] += 1

    trend = [
        {"date": (datetime.datetime.utcnow() - datetime.timedelta(days=d)).strftime("%b %d"), "count": random.randint(1, 4)}
        for d in range(6, -1, -1)
    ]

    return {
        "total": total,
        "by_status": by_status,
        "by_severity": by_severity,
        "by_source": by_source,
        "by_location": by_location,
        "avg_response_minutes": 14.5,
        "trend": trend,
        "date_range": {"start": start_date, "end": end_date}
    }

@app.get("/api/reports/incidents")
def get_report_incidents(
    status: Optional[str] = None,
    severity: Optional[str] = None,
    camera: Optional[str] = None,
    source: Optional[str] = None,
    skip: int = 0,
    limit: int = 50
):
    results = INCIDENTS
    if status:
        results = [i for i in results if i.get("status") == status]
    if camera:
        results = [i for i in results if i.get("camera_id") == camera]
    if source:
        results = [i for i in results if i.get("source") == source]
    return {"total": len(results), "incidents": results[skip:skip+limit], "skip": skip, "limit": limit}

@app.get("/api/reports/incidents/{incident_id}/detail")
def get_report_incident_detail(incident_id: str):
    inc = next((i for i in INCIDENTS if i.get("id") == incident_id), None)
    if not inc:
        return {"error": "Incident not found"}
    return {
        **inc,
        "timeline": [
            {"id": 1, "event_type": "DETECTED", "timestamp": inc.get("timestamp"), "details": "Incident detected"},
            {"id": 2, "event_type": "REVIEW", "timestamp": inc.get("timestamp"), "details": "Review initiated"}
        ]
    }

@app.post("/api/detection/detect")
def detect_objects(payload: dict):
    cam_id = payload.get("camera_id", "CAM-01")
    ts = float(payload.get("timestamp", 0.0) or 0.0)
    w = int(payload.get("width", 640) or 640)
    h = int(payload.get("height", 360) or 360)

    detections = []
    # Camera-specific detections synchronized to demonstration videos
    if cam_id == "CAM-01":
        # Block A - Ground Floor: Pedestrians walking, person falling/requiring assistance
        # Cycle over roughly 14 seconds
        t_mod = ts % 14.0
        # Pedestrian 1
        p1_x = int(w * (0.20 + (t_mod * 0.04) % 0.50))
        p1_y = int(h * 0.28)
        detections.append({
            "id": "TRK-01A",
            "label": "person",
            "display_label": "PERSON",
            "confidence": 94.8,
            "box": [p1_x, p1_y, int(w * 0.11), int(h * 0.45)],
            "is_incident": False,
        })
        # Person fall / assistance event (visible midway in the video)
        is_fall = t_mod >= 4.0 and t_mod <= 12.0
        fall_x = int(w * 0.52)
        fall_y = int(h * 0.42 if is_fall else h * 0.32)
        fall_h = int(h * 0.28 if is_fall else h * 0.44)
        fall_w = int(w * 0.18 if is_fall else w * 0.12)
        detections.append({
            "id": "TRK-01B",
            "label": "fall_detected" if is_fall else "person",
            "display_label": "FALL / ASSISTANCE REQUIRED" if is_fall else "PERSON",
            "confidence": 92.4 if is_fall else 95.1,
            "box": [fall_x, fall_y, fall_w, fall_h],
            "is_incident": is_fall,
            "incident_type": "PERSON_FALL" if is_fall else None,
            "severity": "High" if is_fall else None,
        })

    elif cam_id == "CAM-02":
        # Block B - Corridor: Crowd congestion
        t_mod = ts % 16.0
        is_crowd = t_mod >= 3.0 and t_mod <= 14.0
        detections.append({
            "id": "TRK-02A",
            "label": "person",
            "display_label": "PERSON",
            "confidence": 93.1,
            "box": [int(w * 0.25), int(h * 0.30), int(w * 0.10), int(h * 0.42)],
            "is_incident": False,
        })
        detections.append({
            "id": "TRK-02B",
            "label": "person",
            "display_label": "PERSON",
            "confidence": 91.5,
            "box": [int(w * 0.38), int(h * 0.32), int(w * 0.09), int(h * 0.40)],
            "is_incident": False,
        })
        detections.append({
            "id": "TRK-02C",
            "label": "person",
            "display_label": "PERSON",
            "confidence": 89.7,
            "box": [int(w * 0.50), int(h * 0.28), int(w * 0.11), int(h * 0.44)],
            "is_incident": False,
        })
        if is_crowd:
            detections.append({
                "id": "TRK-02-CLUSTER",
                "label": "crowd_congestion",
                "display_label": "CROWD CONGESTION (8+ PERS)",
                "confidence": 88.9,
                "box": [int(w * 0.22), int(h * 0.24), int(w * 0.44), int(h * 0.52)],
                "is_incident": True,
                "incident_type": "CROWD_CONGESTION",
                "severity": "Low",
            })

    elif cam_id == "CAM-03":
        # Main Gate - Restricted Area Entry
        t_mod = ts % 15.0
        is_breach = t_mod >= 5.0 and t_mod <= 13.0
        gate_x = int(w * (0.30 + (t_mod * 0.035) % 0.40))
        detections.append({
            "id": "TRK-03A",
            "label": "restricted_entry" if is_breach else "person",
            "display_label": "RESTRICTED ZONE BREACH" if is_breach else "PERSON",
            "confidence": 95.8 if is_breach else 93.0,
            "box": [gate_x, int(h * 0.30), int(w * 0.14), int(h * 0.48)],
            "is_incident": is_breach,
            "incident_type": "RESTRICTED_ZONE" if is_breach else None,
            "severity": "High" if is_breach else None,
        })

    elif cam_id == "CAM-04":
        # Canteen - Crowd or Safety Hazard
        t_mod = ts % 18.0
        is_hazard = t_mod >= 4.0 and t_mod <= 15.0
        detections.append({
            "id": "TRK-04A",
            "label": "person",
            "display_label": "PERSON",
            "confidence": 92.0,
            "box": [int(w * 0.20), int(h * 0.32), int(w * 0.12), int(h * 0.42)],
            "is_incident": False,
        })
        detections.append({
            "id": "TRK-04B",
            "label": "person",
            "display_label": "PERSON",
            "confidence": 90.4,
            "box": [int(w * 0.65), int(h * 0.35), int(w * 0.11), int(h * 0.38)],
            "is_incident": False,
        })
        if is_hazard:
            detections.append({
                "id": "TRK-04-HAZARD",
                "label": "safety_hazard",
                "display_label": "SAFETY HAZARD / SPILL",
                "confidence": 87.5,
                "box": [int(w * 0.42), int(h * 0.48), int(w * 0.22), int(h * 0.28)],
                "is_incident": True,
                "incident_type": "SAFETY_HAZARD",
                "severity": "Medium",
            })

    return {
        "camera_id": cam_id,
        "timestamp": ts,
        "inference_ms": 16.5,
        "model": "YOLOv8n-Campus-CV",
        "detections": detections,
    }

@app.post("/api/incidents/{incident_id}/action")
def update_incident_action(incident_id: str, payload: dict):
    inc = next((i for i in INCIDENTS if i.get("id") == incident_id), None)
    if not inc:
        return {"error": "Incident not found"}
    action = payload.get("action")
    now_str = datetime.datetime.utcnow().isoformat()
    actor = payload.get("actor", "Security Officer")
    if action == "ACKNOWLEDGE":
        inc["status"] = "ACKNOWLEDGED"
        inc["acknowledged_at"] = now_str
    elif action == "CONFIRM":
        inc["status"] = "ACKNOWLEDGED"
        inc["review_status"] = "CONFIRMED"
    elif action == "FALSE_ALARM":
        inc["status"] = "FALSE_ALARM"
        inc["review_status"] = "DISMISSED"
    elif action == "ASSIGN":
        inc["assigned_responder"] = payload.get("responder", "Campus Patrol Unit 1")
    elif action == "RESOLVE":
        inc["status"] = "RESOLVED"
        inc["resolved_at"] = now_str

    if "action_history" not in inc:
        inc["action_history"] = []
    inc["action_history"].append({
        "timestamp": now_str,
        "action": f"{action}: {payload.get('note', '')}".strip(": "),
        "actor": actor
    })
    return {"status": "success", "incident": inc}

@app.post("/api/simulator/scenario/{name}")
def run_scenario(name: str):
    name = name.lower()
    now_str = datetime.datetime.utcnow().isoformat()
    if name == "a":
        inc = {
            "id": f"INC-SIM-A-{random.randint(100, 999)}",
            "event_type": "PERSON_FALL",
            "camera_id": "CAM-02",
            "location": "Block B - Corridor",
            "confidence": 92.5,
            "timestamp": now_str,
            "status": "ACTIVE",
            "source": "DEMO",
            "description": "Scenario A: Fall detection triggered. Responder dispatched and incident confirmed."
        }
        INCIDENTS.insert(0, inc)
        return {"status": "Scenario A executed successfully", "incident": inc}
    elif name == "b":
        inc = {
            "id": f"INC-SIM-B-{random.randint(100, 999)}",
            "event_type": "FIGHT",
            "camera_id": "CAM-03",
            "location": "Main Gate",
            "confidence": 96.0,
            "timestamp": now_str,
            "status": "ACTIVE",
            "source": "DEMO",
            "description": "Scenario B: Critical incident escalated to backup responder due to timeout."
        }
        INCIDENTS.insert(0, inc)
        return {"status": "Scenario B executed - Escalation simulated", "incident": inc}
    elif name == "c":
        inc = {
            "id": f"INC-SIM-C-{random.randint(100, 999)}",
            "event_type": "SUSPICIOUS",
            "camera_id": "CAM-04",
            "location": "Cafeteria",
            "confidence": 64.0,
            "timestamp": now_str,
            "status": "FALSE_ALARM",
            "source": "DEMO",
            "description": "Scenario C: False alarm verified and dismissed by operator."
        }
        INCIDENTS.insert(0, inc)
        return {"status": "Scenario C executed - False alarm recorded", "incident": inc}
    return {"status": "error", "message": "Unknown scenario"}

@app.post("/api/simulator/reset")
def reset_demo():
    global INCIDENTS
    INCIDENTS = [
        {
            "id": "INC-RESET-01",
            "event_type": "PERSON_FALL",
            "camera_id": "CAM-01",
            "location": "Block A - Ground Floor",
            "confidence": 94.2,
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "status": "ACTIVE",
            "source": "AI_MODEL",
            "description": "Reset state: Person fall detected at Block A."
        }
    ]
    return {"status": "reset complete", "incidents": INCIDENTS}
