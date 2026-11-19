from app.database import Base
from app.utils import new_uuid
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy import func
from sqlalchemy.orm import relationship


class QueueTicket(Base):
    __tablename__ = "queue_tickets"

    id = Column(String(36), primary_key=True, default=new_uuid)
    request_id = Column(
        String(36), ForeignKey("care_requests.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    unit_id = Column(
        String(36), ForeignKey("healthcare_units.id", ondelete="CASCADE"), nullable=False, index=True
    )
    position = Column(Integer, default=0, nullable=False)
    status = Column(String(20), default="waiting", nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    request = relationship("CareRequest", back_populates="ticket")
    events = relationship("QueueEvent", back_populates="ticket", cascade="all, delete-orphan")


class QueueEvent(Base):
    __tablename__ = "queue_events"

    id = Column(String(36), primary_key=True, default=new_uuid)
    ticket_id = Column(
        String(36), ForeignKey("queue_tickets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    event_type = Column(String(40), nullable=False)
    from_status = Column(String(30))
    to_status = Column(String(30))
    actor_user_id = Column(String(36))
    note = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    ticket = relationship("QueueTicket", back_populates="events")


class CheckIn(Base):
    __tablename__ = "check_ins"

    id = Column(String(36), primary_key=True, default=new_uuid)
    request_id = Column(
        String(36), ForeignKey("care_requests.id", ondelete="CASCADE"), nullable=False, index=True
    )
    unit_id = Column(
        String(36), ForeignKey("healthcare_units.id", ondelete="CASCADE"), nullable=False, index=True
    )
    checked_in_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    method = Column(String(20), default="digital", nullable=False)  # digital | desk
    operator_id = Column(String(36))


class Attendance(Base):
    __tablename__ = "attendances"

    id = Column(String(36), primary_key=True, default=new_uuid)
    request_id = Column(
        String(36), ForeignKey("care_requests.id", ondelete="CASCADE"), nullable=False, index=True
    )
    unit_id = Column(
        String(36), ForeignKey("healthcare_units.id", ondelete="CASCADE"), nullable=False, index=True
    )
    started_at = Column(DateTime(timezone=True), nullable=False)
    finished_at = Column(DateTime(timezone=True))
    duration_minutes = Column(Integer)
    outcome = Column(String(50))  # released | referred | hospitalized | other
    professional_id = Column(String(36))
    notes = Column(Text)
    risk_classification = Column(String(20))  # registrado por profissional
    classification_protocol = Column(String(50))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
