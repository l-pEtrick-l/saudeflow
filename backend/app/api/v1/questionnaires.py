from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user_optional, require_roles
from app.schemas.common import PageMeta
from app.schemas.questionnaire import (
    AnswerIn,
    GuidanceResultOut,
    QuestionOut,
    SubmissionOut,
)
from app.services import guidance_service, questionnaire_service

router = APIRouter(prefix="/questionnaires", tags=["Questionário inteligente"])


class NextQuestionsIn(BaseModel):
    answers: Dict[str, Any] = {}


class AnswersIn(BaseModel):
    answers: list[AnswerIn]


class CompleteIn(BaseModel):
    user_id: Optional[str] = None


@router.get("/active")
def active(db: Session = Depends(get_db), user=Depends(get_current_user_optional)):
    return questionnaire_service.start(db, user.id if user else None)


@router.post("/versions/{version_id}/next", response_model=list[QuestionOut])
def next_questions(
    version_id: str,
    payload: NextQuestionsIn,
    db: Session = Depends(get_db),
):
    return questionnaire_service.get_next_questions(db, version_id, payload.answers)


@router.post("/submissions", response_model=dict)
def create_submission(
    db: Session = Depends(get_db), user=Depends(get_current_user_optional)
):
    return questionnaire_service.start(db, user.id if user else None)


@router.get("/submissions/{submission_id}", response_model=SubmissionOut)
def get_submission(
    submission_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user_optional),
):
    return questionnaire_service.get_submission(
        db, submission_id, user.id if user else None
    )


@router.post("/submissions/{submission_id}/answers", response_model=SubmissionOut)
def submit_answers(
    submission_id: str,
    payload: AnswersIn,
    db: Session = Depends(get_db),
    user=Depends(get_current_user_optional),
):
    return questionnaire_service.submit_answers(
        db, submission_id, payload.answers, user.id if user else None
    )


@router.post("/submissions/{submission_id}/complete", response_model=GuidanceResultOut)
def complete(
    submission_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user_optional),
):
    return questionnaire_service.complete(db, submission_id, user.id if user else None)


@router.get("/submissions/{submission_id}/result", response_model=GuidanceResultOut)
def result(
    submission_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user_optional),
):
    return questionnaire_service.get_result(
        db, submission_id, user.id if user else None
    )


@router.get("/rules")
def rules(
    version: str | None = None,
    db: Session = Depends(get_db),
    _admin=Depends(require_roles("admin")),
):
    return [
        {
            "id": r.id,
            "name": r.name,
            "priority": r.priority,
            "category": r.category,
            "conditions": r.conditions,
            "alert_flags": r.alert_flags,
            "stop_flow": r.stop_flow,
            "confidence": r.confidence,
            "rule_set_version": r.rule_set_version,
        }
        for r in guidance_service.list_rules(db, version)
    ]
