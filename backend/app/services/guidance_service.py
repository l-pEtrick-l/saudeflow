from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.exceptions import NotFoundError
from app.models.guidance import GuidanceResult, GuidanceRule
from app.repositories import guidance_repo
from app.schemas.questionnaire import GuidanceResultOut


def list_rules(db: Session, version: Optional[str] = None) -> List[GuidanceRule]:
    return guidance_repo.list_rules(db, version)


def _rule_to_dict(rule: GuidanceRule) -> Dict[str, Any]:
    return {
        "id": rule.id,
        "name": rule.name,
        "priority": rule.priority,
        "category": rule.category,
        "service_hint": rule.service_hint,
        "conditions": rule.conditions or {},
        "alert_flags": rule.alert_flags or [],
        "confidence": rule.confidence,
        "recommended_unit_types": rule.recommended_unit_types or [],
        "stop_flow": rule.stop_flow,
        "needs_professional": rule.needs_professional,
        "message_template": rule.message_template,
        "rule_set_version": rule.rule_set_version,
        "is_active": rule.is_active,
    }


def load_active_rules(db: Session) -> tuple:
    """Retorna (versão do conjunto de regras, regras ativas ordenadas)."""
    rules = guidance_repo.list_rules(db)
    if not rules:
        return "sem-regras", []
    version = rules[0].rule_set_version
    return version, [_rule_to_dict(r) for r in rules]


def evaluate_submission(db: Session, submission_id: str) -> GuidanceResult:
    """Executa o motor de orientação para uma submissão completa."""
    from app.repositories import questionnaire_repo
    from app.services import guidance_engine

    submission = questionnaire_repo.get_submission(db, submission_id)
    if not submission:
        raise NotFoundError("Submissão não encontrada")
    version = questionnaire_repo.get_version(db, submission.version_id)
    if not version:
        raise NotFoundError("Versão do questionário não encontrada")

    questions = questionnaire_repo.questions_to_dicts(db, version.id)
    answers = questionnaire_repo.answers_map(db, submission_id)
    free_text = str(answers.get("description") or "")

    rule_version, rules = load_active_rules(db)
    result = guidance_engine.evaluate_guidance(
        rules=rules,
        answers=answers,
        questions=questions,
        free_text=free_text,
        rule_set_version=rule_version,
    )
    return guidance_repo.create_result(db, submission_id, result)


def get_result(db: Session, submission_id: str) -> GuidanceResultOut:
    result = guidance_repo.get_result(db, submission_id)
    if not result:
        raise NotFoundError("Orientação ainda não gerada para esta submissão")
    return _result_to_out(result)


def _result_to_out(result: GuidanceResult) -> GuidanceResultOut:
    from app.services.guidance_engine import CATEGORY_LABELS

    service_labels = {
        "atencao_basica": "Atenção básica (UBS)",
        "upa": "UPA / pronto atendimento",
        "hospital": "Hospital / pronto-socorro",
        "emergencia": "Emergência (SAMU 192)",
    }
    return GuidanceResultOut(
        submission_id=result.submission_id,
        category=result.category,
        category_label=CATEGORY_LABELS.get(result.category, result.category),
        service_type=result.service_type,
        service_label=service_labels.get(result.service_type or "", result.service_type or ""),
        alert_flags=result.alert_flags or [],
        justification=result.justification or "",
        confidence=result.confidence,
        stop_flow=result.stop_flow,
        needs_professional=result.needs_professional,
        recommended_unit_types=result.recommended_unit_types or [],
        rule_set_version=result.rule_set_version,
        matched_rule_name=result.matched_rule_name,
        emergency_message=result.emergency_message if result.stop_flow else None,
        created_at=result.created_at,
    )
