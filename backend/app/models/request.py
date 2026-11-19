from app.database import Base
from app.utils import new_uuid
from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy import func
from sqlalchemy.orm import relationship


class ProtocolCounter(Base):
    """Contador transacional para protocolos únicos (SF-AAAA-NNNNNN)."""

    __tablename__ = "protocol_counters"

    year = Column(Integer, primary_key=True)
    seq = Column(Integer, default=0, nullable=False)


class CareRequest(Base):
    __tablename__ = "care_requests"

    id = Column(String(36), primary_key=True, default=new_uuid)
    protocol = Column(String(30), unique=True, nullable=False, index=True)
    submission_id = Column(
        String(36),
        ForeignKey("questionnaire_submissions.id", ondelete="SET NULL"),
        index=True,
    )
    patient_user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), index=True)
    patient_name = Column(String(200), nullable=False)
    patient_phone = Column(String(30))
    patient_birth_date = Column(Date)
    unit_id = Column(
        String(36), ForeignKey("healthcare_units.id", ondelete="CASCADE"), nullable=False, index=True
    )
    category = Column(String(1), nullable=False)  # A | B | C | D
    status = Column(String(30), default="sent", nullable=False, index=True)
    complaint_summary = Column(Text)
    cancellation_reason = Column(Text)
    risk_classification = Column(String(20))  # registrado por profissional presencial
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    deleted_at = Column(DateTime(timezone=True))

    ticket = relationship("QueueTicket", back_populates="request", uselist=False)
    events = relationship("RequestEvent", back_populates="request", cascade="all, delete-orphan")


class RequestEvent(Base):
    __tablename__ = "request_events"

    id = Column(String(36), primary_key=True, default=new_uuid)
    request_id = Column(
        String(36), ForeignKey("care_requests.id", ondelete="CASCADE"), nullable=False, index=True
    )
    event_type = Column(String(40), nullable=False)
    from_status = Column(String(30))
    to_status = Column(String(30))
    actor_user_id = Column(String(36))
    note = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    request = relationship("CareRequest", back_populates="events")
