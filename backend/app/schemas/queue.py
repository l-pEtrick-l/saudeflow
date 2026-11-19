from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from app.schemas.common import ORMModel


class QueueTicketOut(ORMModel):
    id: str
    request_id: str
    unit_id: str
    position: int
    status: str
    protocol: Optional[str] = None
    patient_name: Optional[str] = None
    category: Optional[str] = None
    complaint_summary: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class QueueBoardOut(BaseModel):
    unit_id: str
    unit_name: str
    capacity: dict
    estimate: dict
    tickets: List[QueueTicketOut]


class QueueEventOut(ORMModel):
    id: str
    ticket_id: str
    event_type: str
    from_status: Optional[str] = None
    to_status: Optional[str] = None
    actor_user_id: Optional[str] = None
    note: Optional[str] = None
    created_at: datetime


class CheckInIn(BaseModel):
    method: str = "desk"


class CallNextOut(BaseModel):
    called: Optional[QueueTicketOut] = None
    message: str
