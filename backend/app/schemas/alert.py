from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class AlertCreate(BaseModel):
    destination_unit_id: str
    description: Optional[str] = Field(None, max_length=2000)
    occurred_at: Optional[str] = None
    patient_conscious: str = Field("unknown", pattern="^(yes|no|unknown)$")
    patient_breathing: str = Field("unknown", pattern="^(yes|no|unknown)$")
    bleeding: str = Field("unknown", pattern="^(yes|no|unknown)$")
    current_situation: Optional[str] = None
    eta_minutes: Optional[int] = Field(None, ge=0, le=1440)
    reporter_name: Optional[str] = Field(None, max_length=200)
    reporter_phone: Optional[str] = Field(None, max_length=30)


class AlertUpdate(BaseModel):
    status: str = Field(..., pattern="^(new|received|confirmed|arrived|closed|cancelled)$")
    note: Optional[str] = None


class AlertOut(ORMModel):
    id: str
    alert_code: str
    destination_unit_id: str
    destination_unit_name: Optional[str] = None
    description: Optional[str] = None
    occurred_at: Optional[datetime] = None
    patient_conscious: str
    patient_breathing: str
    bleeding: str
    current_situation: Optional[str] = None
    eta_minutes: Optional[int] = None
    alert_flags: List[str]
    status: str
    status_label: str
    created_at: datetime
    updated_at: datetime
    events: List["AlertEventOut"] = []


class AlertEventOut(ORMModel):
    id: str
    event_type: str
    note: Optional[str] = None
    actor_user_id: Optional[str] = None
    created_at: datetime


AlertOut.model_rebuild()
