from app.database import Base
from app.utils import new_uuid
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy import func
from sqlalchemy.orm import relationship


class EmergencyAlert(Base):
    __tablename__ = "emergency_alerts"

    id = Column(String(36), primary_key=True, default=new_uuid)
    alert_code = Column(String(30), unique=True, nullable=False, index=True)
    submission_id = Column(
        String(36), ForeignKey("questionnaire_submissions.id", ondelete="SET NULL"), index=True
    )
    reporter_user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), index=True)
    destination_unit_id = Column(
        String(36),
        ForeignKey("healthcare_units.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    description = Column(Text)
    occurred_at = Column(DateTime(timezone=True))
    patient_conscious = Column(String(10), default="unknown")  # yes | no | unknown
    patient_breathing = Column(String(10), default="unknown")
    bleeding = Column(String(10), default="unknown")
    current_situation = Column(Text)
    eta_minutes = Column(Integer)
    alert_flags = Column(JSON, default=list)
    status = Column(String(20), default="new", nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    events = relationship(
        "EmergencyAlertEvent", back_populates="alert", cascade="all, delete-orphan"
    )


class EmergencyAlertEvent(Base):
    __tablename__ = "emergency_alert_events"

    id = Column(String(36), primary_key=True, default=new_uuid)
    alert_id = Column(
        String(36),
        ForeignKey("emergency_alerts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_type = Column(String(40), nullable=False)
    note = Column(Text)
    actor_user_id = Column(String(36))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    alert = relationship("EmergencyAlert", back_populates="events")
