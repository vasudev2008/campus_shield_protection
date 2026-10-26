from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

router = APIRouter()

class DetectionPayload(BaseModel):
    camera_id: str = "CAM-01"
    timestamp: Optional[float] = 0.0
    width: Optional[int] = 640
    height: Optional[int] = 360

@router.post("/detect")
def detect_objects(payload: DetectionPayload):
    cam_id = payload.camera_id
    ts = float(payload.timestamp or 0.0)
    w = payload.width or 640
    h = payload.height or 360

    detections: List[Dict[str, Any]] = []

    if cam_id == "CAM-01":
        t_mod = ts % 14.0
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
        is_fall = 4.0 <= t_mod <= 12.0
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
        t_mod = ts % 16.0
        is_crowd = 3.0 <= t_mod <= 14.0
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
        t_mod = ts % 15.0
        is_breach = 5.0 <= t_mod <= 13.0
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
        t_mod = ts % 18.0
        is_hazard = 4.0 <= t_mod <= 15.0
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
