from app.database import Base
from app.utils import new_uuid
from sqlalchemy import (
    Column,
    DateTime,
    JSON,
    String,
    Text,
)
from sqlalchemy import func


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=new_uuid)
    actor_user_id = Column(String(36), index=True)
    action = Column(String(80), nullable=False, index=True)
    entity_type = Column(String(60), index=True)
    entity_id = Column(String(36), index=True)
    details = Column(JSON)
    ip_address = Column(String(64))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
