from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.exceptions import ForbiddenError, NotFoundError, UnprocessableError
from app.models.questionnaire import QuestionnaireSubmission
from app.repositories import questionnaire_repo
from app.schemas.questionnaire import (
    AnswerIn,
    GuidanceResultOut,
    QuestionOut,
    SubmissionOut,
)
from app.services import guidance_service


def _submission_out(submission: QuestionnaireSubmission, db: Session) -> SubmissionOut:
    answers = questionnaire_repo.list_answer_entities(db, submission.id)
    return SubmissionOut(
        id=submission.id,
        version_id=submission.version_id,
        user_id=submission.user_id,
        session_token=submission.session_token,
        status=submission.status,
        created_at=submission.created_at,
        completed_at=submission.completed_at,
        answers=[
            {
                "id": a.id,
                "question_id": a.question_id,
                "value_text": a.value_text,
                "value_json": a.value_json,
                "answered_at": a.answered_at,
            }
            for a in answers
        ],
    )


def start(db: Session, user_id: Optional[str] = None, session_token: Optional[str] = None):
    version = questionnaire_repo.get_active_version(db)
    if not version:
        raise UnprocessableError(
            "Nenhum questionário publicado", code="no_questionnaire"
        )
    submission = questionnaire_repo.create_submission(
        db, version.id, user_id, session_token
    )
    questions = questionnaire_repo.questions_to_dicts(db, version.id)
    return {
        "submission": _submission_out(submission, db),
        "rule_set_version": version.rule_set_version,
        "questions": [
            QuestionOut.model_validate(q)
            for q in _visible_questions(questions, {})
        ],
    }


def get_next_questions(
    db: Session, version_id: str, answers: Dict[str, Any]
) -> List[QuestionOut]:
    questions = questionnaire_repo.questions_to_dicts(db, version_id)
    return [
        QuestionOut.model_validate(q) for q in _visible_questions(questions, answers)
    ]


def _visible_questions(questions: List[dict], answers: Dict[str, Any]) -> List[dict]:
    from app.services.guidance_engine import visible_questions

    return visible_questions(questions, answers)


def submit_answers(
    db: Session,
    submission_id: str,
    answers: List[AnswerIn],
    user_id: Optional[str] = None,
) -> SubmissionOut:
    submission = _get_owned_submission(db, submission_id, user_id)
    if submission.status == "completed":
        raise UnprocessableError("Questionário já concluído", code="already_completed")
    valid_questions = {
        q["id"]
        for q in questionnaire_repo.questions_to_dicts(db, submission.version_id)
    }
    for answer in answers:
        if answer.question_id not in valid_questions:
            raise UnprocessableError(
                f"Pergunta inválida: {answer.question_id}", code="invalid_question"
            )
        questionnaire_repo.add_answer(
            db, submission_id, answer.question_id, answer.value
        )
    db.refresh(submission)
    return _submission_out(submission, db)


def complete(db: Session, submission_id: str, user_id: Optional[str] = None) -> GuidanceResultOut:
    submission = _get_owned_submission(db, submission_id, user_id)
    if submission.status == "completed":
        return guidance_service.get_result(db, submission_id)
    answers = questionnaire_repo.answers_map(db, submission_id)
    if not answers:
        raise UnprocessableError(
            "Responda ao menos uma pergunta antes de concluir",
            code="empty_submission",
        )
    questionnaire_repo.set_status(db, submission, "completed")
    result = guidance_service.evaluate_submission(db, submission_id)
    return guidance_service.get_result(db, submission_id)


def get_result(db: Session, submission_id: str, user_id: Optional[str] = None) -> GuidanceResultOut:
    _get_owned_submission(db, submission_id, user_id)
    return guidance_service.get_result(db, submission_id)


def get_submission(db: Session, submission_id: str, user_id: Optional[str] = None) -> SubmissionOut:
    submission = _get_owned_submission(db, submission_id, user_id)
    return _submission_out(submission, db)


def _get_owned_submission(
    db: Session, submission_id: str, user_id: Optional[str]
) -> QuestionnaireSubmission:
    submission = questionnaire_repo.get_submission(db, submission_id)
    if not submission:
        raise NotFoundError("Submissão não encontrada")
    if submission.user_id and user_id and submission.user_id != user_id:
        raise ForbiddenError("Você não pode acessar este questionário")
    return submission
