from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    actor_user_id: Optional[str] = None
    action: str
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    details: Optional[Any] = None
    ip_address: Optional[str] = None
    created_at: datetime
