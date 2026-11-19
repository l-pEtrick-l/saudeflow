from app.database import Base
from app.utils import new_uuid
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy import func


class WaitEstimate(Base):
    """Estimativa operacional por unidade (cache calculado pelo serviço Estimates)."""

    __tablename__ = "wait_estimates"

    id = Column(String(36), primary_key=True, default=new_uuid)
    unit_id = Column(
        String(36), ForeignKey("healthcare_units.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    low_minutes = Column(Float)
    p50_minutes = Column(Float)
    high_minutes = Column(Float)
    sample_size = Column(Integer, default=0, nullable=False)
    method = Column(String(50))
    is_reliable = Column(Boolean, default=False, nullable=False)
    computed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
