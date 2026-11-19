from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.questionnaire import (
    Question,
    QuestionOption,
    Questionnaire,
    QuestionnaireAnswer,
    QuestionnaireSubmission,
    QuestionnaireVersion,
)
from app.repositories.base import get_or_404
from app.utils import new_uuid


def get_active_questionnaire(db: Session) -> Optional[Questionnaire]:
    return db.scalar(
        select(Questionnaire)
        .filter(Questionnaire.is_active.is_(True))
        .order_by(Questionnaire.created_at.desc())
    )


def get_active_version(db: Session) -> Optional[QuestionnaireVersion]:
    questionnaire = get_active_questionnaire(db)
    if not questionnaire:
        return None
    return db.scalar(
        select(QuestionnaireVersion)
        .filter_by(questionnaire_id=questionnaire.id, status="published")
        .order_by(QuestionnaireVersion.version.desc())
    )


def get_version(db: Session, version_id: str) -> Optional[QuestionnaireVersion]:
    return db.get(QuestionnaireVersion, version_id)


def get_questions(db: Session, version_id: str) -> List[Question]:
    return db.scalars(
        select(Question)
        .filter_by(version_id=version_id)
        .order_by(Question.order_index, Question.id)
    ).all()


def question_to_dict(db: Session, question: Question) -> Dict[str, Any]:
    options = db.scalars(
        select(QuestionOption)
        .filter_by(question_id=question.id)
        .order_by(QuestionOption.order_index)
    ).all()
    return {
        "id": question.id,
        "external_id": question.external_id,
        "text": question.text,
        "type": question.type,
        "required": question.required,
        "order_index": question.order_index,
        "help_text": question.help_text,
        "conditional_logic": question.conditional_logic,
        "alert_flags": question.alert_flags or [],
        "options": [
            {
                "id": o.id,
                "code": o.code,
                "label": o.label,
                "order_index": o.order_index,
                "alert_flag": o.alert_flag,
            }
            for o in options
        ],
    }


def questions_to_dicts(db: Session, version_id: str) -> List[Dict[str, Any]]:
    return [question_to_dict(db, q) for q in get_questions(db, version_id)]


def create_submission(
    db: Session,
    version_id: str,
    user_id: Optional[str],
    session_token: Optional[str] = None,
) -> QuestionnaireSubmission:
    submission = QuestionnaireSubmission(
        version_id=version_id,
        user_id=user_id,
        session_token=session_token or new_uuid(),
        status="in_progress",
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)
    return submission


def get_submission(db: Session, submission_id: str) -> Optional[QuestionnaireSubmission]:
    return db.get(QuestionnaireSubmission, submission_id)


def add_answer(
    db: Session, submission_id: str, question_id: str, value: Any
) -> QuestionnaireAnswer:
    existing = db.scalar(
        select(QuestionnaireAnswer).filter_by(
            submission_id=submission_id, question_id=question_id
        )
    )
    value_json = value if isinstance(value, (dict, list, int, float, bool)) else None
    value_text = None if value_json is not None else (str(value) if value is not None else None)
    if existing:
        existing.value_json = value_json
        existing.value_text = value_text
        existing.answered_at = datetime.now(timezone.utc)
        answer = existing
    else:
        answer = QuestionnaireAnswer(
            submission_id=submission_id,
            question_id=question_id,
            value_json=value_json,
            value_text=value_text,
        )
        db.add(answer)
    db.commit()
    db.refresh(answer)
    return answer


def answers_map(db: Session, submission_id: str) -> Dict[str, Any]:
    rows = db.scalars(
        select(QuestionnaireAnswer).filter_by(submission_id=submission_id)
    ).all()
    result: Dict[str, Any] = {}
    questions = {q.id: q.external_id for q in db.scalars(select(Question)).all()}
    for row in rows:
        external = questions.get(row.question_id, row.question_id)
        result[external] = row.value_json if row.value_json is not None else row.value_text
    return result


def list_answer_entities(db: Session, submission_id: str) -> List[QuestionnaireAnswer]:
    return db.scalars(
        select(QuestionnaireAnswer).filter_by(submission_id=submission_id)
    ).all()


def set_status(db: Session, submission: QuestionnaireSubmission, status: str) -> None:
    submission.status = status
    if status == "completed":
        submission.completed_at = datetime.now(timezone.utc)
    db.commit()
