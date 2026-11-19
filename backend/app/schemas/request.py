from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field

from app.schemas.common import ORMModel


class RequestCreate(BaseModel):
    submission_id: str
    unit_id: str
    patient_name: str = Field(..., min_length=3, max_length=200)
    patient_phone: Optional[str] = Field(None, max_length=30)
    patient_birth_date: Optional[str] = None
    complaint_summary: Optional[str] = None


class RequestOut(ORMModel):
    id: str
    protocol: str
    submission_id: Optional[str] = None
    patient_user_id: Optional[str] = None
    patient_name: str
    patient_phone: Optional[str] = None
    patient_birth_date: Optional[str] = None
    unit_id: str
    unit_name: Optional[str] = None
    category: str
    status: str
    status_label: str
    complaint_summary: Optional[str] = None
    cancellation_reason: Optional[str] = None
    risk_classification: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    ticket: Optional["TicketBrief"] = None


class TicketBrief(BaseModel):
    id: str
    position: int
    status: str


class RequestEventOut(ORMModel):
    id: str
    event_type: str
    from_status: Optional[str] = None
    to_status: Optional[str] = None
    actor_user_id: Optional[str] = None
    note: Optional[str] = None
    created_at: datetime


class CancelIn(BaseModel):
    reason: str = Field(..., min_length=3, max_length=500)


class RiskClassificationIn(BaseModel):
    risk_classification: str = Field(..., min_length=1, max_length=20)
    classification_protocol: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = None


RequestOut.model_rebuild()
