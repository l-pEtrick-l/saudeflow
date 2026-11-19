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
    UniqueConstraint,
)
from sqlalchemy import func


class IntegrationSource(Base):
    __tablename__ = "integration_sources"

    id = Column(String(36), primary_key=True, default=new_uuid)
    code = Column(String(40), unique=True, nullable=False, index=True)
    name = Column(String(120), nullable=False)
    base_url = Column(String(255))
    enabled = Column(Boolean, default=True, nullable=False)
    rate_limit_rpm = Column(Integer, default=60, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class ExternalUnit(Base):
    """Cache local de registros vindos de APIs externas (CNES, DATASUS)."""

    __tablename__ = "external_units"
    __table_args__ = (UniqueConstraint("source", "external_id", name="uq_external_source_id"),)

    id = Column(String(36), primary_key=True, default=new_uuid)
    source = Column(String(40), nullable=False, index=True)  # cnes | datasus_leitos
    external_id = Column(String(60), nullable=False, index=True)
    source_data = Column(JSON)  # payload original (auditável)
    name = Column(String(255), index=True)
    type_code = Column(String(20))
    type_name = Column(String(120))
    street = Column(String(255))
    number = Column(String(20))
    neighborhood = Column(String(120))
    city = Column(String(120), index=True)
    state = Column(String(2), index=True)
    postal_code = Column(String(10))
    latitude = Column(Float)
    longitude = Column(Float)
    phone = Column(String(40))
    cnes_code = Column(String(20), index=True)
    ibge_code = Column(String(20), index=True)
    beds_total = Column(Integer)
    beds_sus = Column(Integer)
    fetched_at = Column(DateTime(timezone=True), nullable=False, index=True)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class SyncLog(Base):
    __tablename__ = "sync_logs"

    id = Column(String(36), primary_key=True, default=new_uuid)
    source = Column(String(40), nullable=False, index=True)
    status = Column(String(20), nullable=False, index=True)  # running | success | partial | failed
    started_at = Column(DateTime(timezone=True), nullable=False)
    finished_at = Column(DateTime(timezone=True))
    records_fetched = Column(Integer, default=0)
    records_inserted = Column(Integer, default=0)
    records_updated = Column(Integer, default=0)
    error = Column(Text)
    triggered_by = Column(String(60))


class IntegrationSetting(Base):
    __tablename__ = "integration_settings"

    key = Column(String(80), primary_key=True)
    value = Column(Text)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
