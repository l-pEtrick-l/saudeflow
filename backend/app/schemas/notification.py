from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: Optional[str] = None
    request_id: Optional[str] = None
    alert_id: Optional[str] = None
    title: str
    body: Optional[str] = None
    type: str
    is_read: bool
    created_at: datetime


class NotificationMarkRead(BaseModel):
    is_read: bool = True
