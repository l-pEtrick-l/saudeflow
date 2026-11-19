from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class QuestionOptionOut(ORMModel):
    id: str
    code: str
    label: str
    order_index: int
    alert_flag: Optional[str] = None


class QuestionOut(ORMModel):
    id: str
    external_id: str
    text: str
    type: str
    required: bool
    order_index: int
    help_text: Optional[str] = None
    options: List[QuestionOptionOut] = []


class SubmissionCreate(BaseModel):
    session_token: Optional[str] = None
    answers: List["AnswerIn"] = []


class AnswerIn(BaseModel):
    question_id: str
    value: Any = None


class AnswerOut(ORMModel):
    id: str
    question_id: str
    value_text: Optional[str] = None
    value_json: Optional[Any] = None
    answered_at: datetime


class SubmissionOut(ORMModel):
    id: str
    version_id: str
    user_id: Optional[str] = None
    session_token: Optional[str] = None
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    answers: List[AnswerOut] = []


class GuidanceResultOut(BaseModel):
    submission_id: str
    category: str
    category_label: str
    service_type: Optional[str] = None
    service_label: str
    alert_flags: List[str]
    justification: str
    confidence: float
    stop_flow: bool
    needs_professional: bool
    recommended_unit_types: List[str]
    rule_set_version: str
    matched_rule_name: Optional[str] = None
    emergency_message: Optional[str] = None
    created_at: Optional[datetime] = None


class GuidanceRuleOut(ORMModel):
    id: str
    rule_set_version: str
    name: str
    description: Optional[str] = None
    priority: int
    category: str
    service_hint: Optional[str] = None
    conditions: Any
    alert_flags: List[str]
    stop_flow: bool
    needs_professional: bool
    message_template: Optional[str] = None
    is_active: bool


SubmissionCreate.model_rebuild()
