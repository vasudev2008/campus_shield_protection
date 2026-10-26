from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey, Enum, Text
from sqlalchemy.orm import relationship
import enum
from datetime import datetime
from ..core.database import Base

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    SECURITY = "security"
    COORDINATOR = "coordinator"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.SECURITY, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class CampusBlock(Base):
    __tablename__ = "campus_blocks"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(Text, nullable=True)
    cameras = relationship("Camera", back_populates="block")

class Camera(Base):
    __tablename__ = "cameras"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    block_id = Column(Integer, ForeignKey("campus_blocks.id"), nullable=False)
    is_available = Column(Boolean, default=True)
    last_heartbeat = Column(DateTime, default=datetime.utcnow)
    processing_status = Column(String, default="idle")
    block = relationship("CampusBlock", back_populates="cameras")

class IncidentStatus(str, enum.Enum):
    DETECTED = "detected"
    UNDER_REVIEW = "under_review"
    CONFIRMED = "confirmed"
    DISPATCHED = "dispatched"
    RESPONDING = "responding"
    RESOLVED = "resolved"
    FALSE_ALARM = "false_alarm"

class Incident(Base):
    __tablename__ = "incidents"
    id = Column(Integer, primary_key=True, index=True)
    category = Column(String, nullable=False)
    block_id = Column(Integer, ForeignKey("campus_blocks.id"), nullable=False)
    location_desc = Column(String, nullable=True)
    severity = Column(Integer, nullable=False)  # 1-5 scale
    detection_timestamp = Column(DateTime, default=datetime.utcnow)
    detection_source = Column(String, nullable=False)  # e.g., AI_MODEL, SIMULATED
    confidence = Column(Float, nullable=True)
    assigned_responder_id = Column(Integer, ForeignKey("responders.id"), nullable=True)
    status = Column(Enum(IncidentStatus), default=IncidentStatus.DETECTED)
    resolution_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    block = relationship("CampusBlock")
    assigned_responder = relationship("Responder", back_populates="incidents")
    events = relationship("IncidentEvent", back_populates="incident", cascade="all, delete-orphan")

class Responder(Base):
    __tablename__ = "responders"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    role = Column(String, nullable=False)  # Security Officer, Backup, etc.
    block_id = Column(Integer, ForeignKey("campus_blocks.id"), nullable=False)
    incidents = relationship("Incident", back_populates="assigned_responder")
    block = relationship("CampusBlock")

class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=False)
    responder_id = Column(Integer, ForeignKey("responders.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    acknowledged_at = Column(DateTime, nullable=True)
    escalated = Column(Boolean, default=False)
    incident = relationship("Incident")
    responder = relationship("Responder")

class IncidentEventType(str, enum.Enum):
    STATE_CHANGE = "state_change"
    ASSIGNMENT = "assignment"
    NOTES = "notes"
    ESCALATION = "escalation"

class IncidentEvent(Base):
    __tablename__ = "incident_events"
    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=False)
    event_type = Column(Enum(IncidentEventType), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    details = Column(Text, nullable=True)
    incident = relationship("Incident", back_populates="events")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    details = Column(Text, nullable=True)
    user = relationship("User")

class NotificationRecord(Base):
    __tablename__ = "notification_records"
    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(Integer, ForeignKey("alerts.id"), nullable=False)
    method = Column(String, nullable=False)  # in_app, email, sms
    status = Column(String, nullable=False)  # sent, failed, pending
    timestamp = Column(DateTime, default=datetime.utcnow)
    alert = relationship("Alert")
