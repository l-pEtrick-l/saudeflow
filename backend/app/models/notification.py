from app.database import Base
from app.utils import new_uuid
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy import func


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String(36), primary_key=True, default=new_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    request_id = Column(String(36), index=True)
    alert_id = Column(String(36), index=True)
    title = Column(String(200), nullable=False)
    body = Column(Text)
    type = Column(String(40), default="info", nullable=False)
    is_read = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
