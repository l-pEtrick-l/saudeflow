from app.database import Base
from app.utils import new_uuid
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy import func


class GuidanceRule(Base):
    """Regra versionada do motor de orientação (demonstrativa, requer validação clínica)."""

    __tablename__ = "guidance_rules"

    id = Column(String(36), primary_key=True, default=new_uuid)
    rule_set_version = Column(String(50), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    priority = Column(Integer, default=100, nullable=False)
    category = Column(String(1), nullable=False)  # A | B | C | D
    service_hint = Column(String(100))
    conditions = Column(JSON, nullable=False)
    alert_flags = Column(JSON, default=list)
    confidence = Column(Float, default=0.5, nullable=False)
    recommended_unit_types = Column(JSON, default=list)
    stop_flow = Column(Boolean, default=False, nullable=False)
    needs_professional = Column(Boolean, default=True, nullable=False)
    message_template = Column(Text)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class GuidanceResult(Base):
    __tablename__ = "guidance_results"

    id = Column(String(36), primary_key=True, default=new_uuid)
    submission_id = Column(
        String(36),
        ForeignKey("questionnaire_submissions.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    rule_set_version = Column(String(50), nullable=False)
    matched_rule_id = Column(String(36), index=True)
    matched_rule_name = Column(String(200))
    category = Column(String(1), nullable=False)
    service_type = Column(String(50))
    alert_flags = Column(JSON, default=list)
    justification = Column(Text)
    confidence = Column(Float, default=0.5, nullable=False)
    stop_flow = Column(Boolean, default=False, nullable=False)
    needs_professional = Column(Boolean, default=True, nullable=False)
    recommended_unit_types = Column(JSON, default=list)
    emergency_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
