from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    ADMIN = "admin"
    SECURITY = "security"
    COORDINATOR = "coordinator"

class UserBase(BaseModel):
    username: str
    full_name: str
    role: UserRole = UserRole.SECURITY
    is_active: bool = True

class UserCreate(UserBase):
    password: str

class UserRead(UserBase):
    id: int

    class Config:
        orm_mode = True

class CampusBlockBase(BaseModel):
    name: str
    description: Optional[str] = None

class CampusBlockCreate(CampusBlockBase):
    pass

class CampusBlockRead(CampusBlockBase):
    id: int

    class Config:
        orm_mode = True

class CameraBase(BaseModel):
    name: str
    block_id: int
    is_available: bool = True
    processing_status: str = "idle"

class CameraCreate(CameraBase):
    pass

class CameraRead(CameraBase):
    id: int
    last_heartbeat: datetime

    class Config:
        orm_mode = True

class IncidentStatus(str, Enum):
    DETECTED = "detected"
    UNDER_REVIEW = "under_review"
    CONFIRMED = "confirmed"
    DISPATCHED = "dispatched"
    RESPONDING = "responding"
    RESOLVED = "resolved"
    FALSE_ALARM = "false_alarm"

class IncidentBase(BaseModel):
    category: str
    block_id: int
    location_desc: Optional[str] = None
    severity: int = Field(..., ge=1, le=5)
    detection_source: str
    confidence: Optional[float] = None

class IncidentCreate(IncidentBase):
    pass

class IncidentRead(IncidentBase):
    id: int
    detection_timestamp: datetime
    assigned_responder_id: Optional[int]
    status: IncidentStatus
    resolution_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class IncidentUpdate(BaseModel):
    status: Optional[IncidentStatus] = None
    assigned_responder_id: Optional[int] = None
    resolution_notes: Optional[str] = None

class ResponderBase(BaseModel):
    name: str
    role: str
    block_id: int

class ResponderCreate(ResponderBase):
    pass

class ResponderRead(ResponderBase):
    id: int

    class Config:
        orm_mode = True

class AlertRead(BaseModel):
    id: int
    incident_id: int
    responder_id: int
    created_at: datetime
    acknowledged_at: Optional[datetime]
    escalated: bool

    class Config:
        orm_mode = True

class IncidentEventType(str, Enum):
    STATE_CHANGE = "state_change"
    ASSIGNMENT = "assignment"
    NOTES = "notes"
    ESCALATION = "escalation"

class IncidentEventBase(BaseModel):
    incident_id: int
    event_type: IncidentEventType
    details: Optional[str] = None

class IncidentEventRead(IncidentEventBase):
    id: int
    timestamp: datetime

    class Config:
        orm_mode = True
