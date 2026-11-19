from typing import List, Optional

from sqlalchemy.orm import Session

from app.exceptions import ConflictError, ForbiddenError, NotFoundError, UnprocessableError
from app.models.request import CareRequest
from app.models.unit import HealthcareUnit
from app.repositories import (
    alert_repo,
    audit_repo,
    notification_repo,
    queue_repo,
    request_repo,
    unit_repo,
    user_repo,
)
from app.schemas.request import (
    CancelIn,
    RequestCreate,
    RequestEventOut,
    RequestOut,
    RiskClassificationIn,
)
from app.realtime import (
    channel_for_request,
    channel_for_unit,
    channel_for_user,
    event_message,
    publish_event,
)
from app.services import estimate_service


def _to_out(db: Session, request: CareRequest) -> RequestOut:
    unit = unit_repo.get_unit(db, request.unit_id)
    ticket = queue_repo.get_ticket_for_request(db, request.id)
    return RequestOut(
        id=request.id,
        protocol=request.protocol,
        submission_id=request.submission_id,
        patient_user_id=request.patient_user_id,
        patient_name=request.patient_name,
        patient_phone=request.patient_phone,
        patient_birth_date=request.patient_birth_date.isoformat() if request.patient_birth_date else None,
        unit_id=request.unit_id,
        unit_name=unit.name if unit else None,
        category=request.category,
        status=request.status,
        status_label=request_repo.STATUS_LABELS.get(request.status, request.status),
        complaint_summary=request.complaint_summary,
        cancellation_reason=request.cancellation_reason,
        risk_classification=request.risk_classification,
        created_at=request.created_at,
        updated_at=request.updated_at,
        ticket=(
            {"id": ticket.id, "position": ticket.position, "status": ticket.status}
            if ticket
            else None
        ),
    )


def create_request(
    db: Session,
    payload: RequestCreate,
    user_id: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> RequestOut:
    unit = unit_repo.get_unit(db, payload.unit_id)
    if not unit or not unit.is_active:
        raise NotFoundError("Unidade não encontrada ou inativa")
    if unit.type == "ubs":
        raise UnprocessableError(
            "UBS não operam fila de pronto atendimento no MVP",
            code="ubs_no_queue",
        )
    submission = db.get(
        __import__("app.models.questionnaire", fromlist=["QuestionnaireSubmission"]).QuestionnaireSubmission,
        payload.submission_id,
    )
    if not submission:
        raise NotFoundError("Submissão de questionário não encontrada")

    # duplicidade: mesmo paciente + mesma unidade + solicitação ativa
    duplicate = db.query(CareRequest).filter(
        CareRequest.unit_id == payload.unit_id,
        CareRequest.patient_name == payload.patient_name,
        CareRequest.status.notin_(["finished", "cancelled"]),
    ).first()
    if duplicate:
        raise ConflictError(
            "Já existe uma solicitação ativa para este paciente nesta unidade",
            code="duplicate_request",
        )

    request = request_repo.create_request(
        db,
        {
            "submission_id": payload.submission_id,
            "patient_user_id": user_id,
            "patient_name": payload.patient_name,
            "patient_phone": payload.patient_phone,
            "patient_birth_date": payload.patient_birth_date,
            "unit_id": payload.unit_id,
            "category": submission_category(db, payload.submission_id),
            "complaint_summary": payload.complaint_summary,
            "status": "sent",
        },
    )
    estimate_service.compute_and_cache(db, payload.unit_id)

    notification_repo.notify_unit_staff(
        db,
        payload.unit_id,
        "Nova solicitação digital",
        f"{request.patient_name} enviou um pré-cadastro ({request.protocol}).",
        type="request",
        request_id=request.id,
    )
    if user_id:
        notification_repo.create(
            db,
            title="Solicitação enviada",
            body=f"Seu protocolo é {request.protocol}. A unidade confirmará o recebimento.",
            type="request",
            user_id=user_id,
            request_id=request.id,
        )
    audit_repo.log(
        db,
        action="request.create",
        entity_type="care_request",
        entity_id=request.id,
        actor_user_id=user_id,
        details={"protocol": request.protocol, "unit_id": payload.unit_id},
        ip_address=ip_address,
    )
    out = _to_out(db, request)
    publish_event(
        channel_for_request(request.id),
        event_message("request_status", out.model_dump(mode="json")),
    )
    publish_event(
        channel_for_unit(payload.unit_id),
        event_message("queue_updated", {"unit_id": payload.unit_id, "protocol": request.protocol}),
    )
    if user_id:
        publish_event(
            channel_for_user(user_id),
            event_message("request_status", out.model_dump(mode="json")),
        )
    return out


def submission_category(db: Session, submission_id: str) -> str:
    from app.repositories import guidance_repo

    result = guidance_repo.get_result(db, submission_id)
    return result.category if result else "B"


def get_request(db: Session, request_id: str, user_id: Optional[str], is_admin: bool = False) -> RequestOut:
    request = request_repo.get_request(db, request_id)
    if not request:
        raise NotFoundError("Solicitação não encontrada")
    if not can_access(db, request, user_id, is_admin):
        raise ForbiddenError("Acesso negado a esta solicitação")
    return _to_out(db, request)


def get_by_protocol(db: Session, protocol: str) -> Optional[CareRequest]:
    return request_repo.get_by_protocol(db, protocol)


def track_request(db: Session, protocol: str) -> dict:
    """Consulta pública e limitada (não expõe relatos de saúde)."""
    request = request_repo.get_by_protocol(db, protocol.upper())
    if not request:
        raise NotFoundError("Protocolo não encontrado")
    unit = unit_repo.get_unit(db, request.unit_id)
    estimate = estimate_service.get_estimate(db, request.unit_id)
    return {
        "protocol": request.protocol,
        "status": request.status,
        "status_label": request_repo.STATUS_LABELS.get(request.status, request.status),
        "unit_name": unit.name if unit else None,
        "unit_city": unit.city if unit else None,
        "category": request.category,
        "created_at": request.created_at,
        "updated_at": request.updated_at,
        "estimate": {
            "is_reliable": estimate.is_reliable,
            "low_minutes": estimate.low_minutes,
            "high_minutes": estimate.high_minutes,
            "message": estimate.message,
        },
    }


def list_requests(
    db: Session,
    user_id: str,
    is_admin: bool,
    unit_ids: List[str],
    page: int,
    page_size: int,
    status: Optional[str] = None,
    unit_id: Optional[str] = None,
):
    if is_admin:
        items, total = request_repo.list_requests(db, page, page_size, unit_id=unit_id, status=status)
    elif unit_ids:
        items, total = [], 0
        for uid in unit_ids:
            page_items, _ = request_repo.list_requests(
                db, page=1, page_size=page_size, unit_id=uid, status=status
            )
            items.extend(page_items)
        items = sorted(items, key=lambda r: r.created_at, reverse=True)
        total = len(items)
        items = items[(page - 1) * page_size : page * page_size]
    else:
        items, total = request_repo.list_requests(
            db, page, page_size, patient_user_id=user_id, status=status
        )
    return [_to_out(db, r) for r in items], total


def update_status(
    db: Session,
    request_id: str,
    status: str,
    actor_id: Optional[str],
    note: Optional[str],
    ip_address: Optional[str] = None,
) -> RequestOut:
    request = request_repo.get_request(db, request_id)
    if not request:
        raise NotFoundError("Solicitação não encontrada")
    request_repo.update_status(db, request, status, actor_id, note)
    _sync_ticket(db, request, status, actor_id, note)
    estimate_service.compute_and_cache(db, request.unit_id)
    out = _to_out(db, request)
    notification_repo.create(
        db,
        title="Atualização da sua solicitação",
        body=f"{request.protocol}: {request_repo.STATUS_LABELS.get(status, status)}",
        type="request",
        user_id=request.patient_user_id,
        request_id=request.id,
    )
    audit_repo.log(
        db,
        action="request.status",
        entity_type="care_request",
        entity_id=request.id,
        actor_user_id=actor_id,
        details={"from": request.status, "to": status},
        ip_address=ip_address,
    )
    publish_event(
        channel_for_request(request.id),
        event_message("request_status", out.model_dump(mode="json")),
    )
    if request.patient_user_id:
        publish_event(
            channel_for_user(request.patient_user_id),
            event_message("request_status", out.model_dump(mode="json")),
        )
    return out


def _sync_ticket(db: Session, request: CareRequest, status: str, actor_id, note):
    ticket = queue_repo.get_ticket_for_request(db, request.id)
    if not ticket:
        return
    mapping = {
        "pre_register_confirmed": ("called", "Pré-cadastro confirmado"),
        "patient_arrived": ("called", "Paciente chegou"),
        "awaiting_welcome": ("attending", "Acolhimento iniciado"),
        "awaiting_care": ("attending", "Aguardando atendimento"),
        "in_care": ("attending", "Atendimento iniciado"),
        "finished": ("done", "Atendimento finalizado"),
        "cancelled": ("cancelled", "Solicitação cancelada"),
    }
    if status in mapping:
        target, label = mapping[status]
        queue_repo.update_ticket(db, ticket, target, actor_user_id=actor_id, note=note or label)


def cancel(
    db: Session,
    request_id: str,
    payload: CancelIn,
    actor_id: Optional[str],
    is_admin: bool = False,
) -> RequestOut:
    request = request_repo.get_request(db, request_id)
    if not request:
        raise NotFoundError("Solicitação não encontrada")
    if request.status in ("finished", "cancelled"):
        raise UnprocessableError("Solicitação já encerrada", code="already_closed")
    if not is_admin and request.patient_user_id != actor_id:
        raise ForbiddenError("Acesso negado")
    request_repo.cancel(db, request, payload.reason, actor_id)
    ticket = queue_repo.get_ticket_for_request(db, request.id)
    if ticket and ticket.status not in ("done", "cancelled"):
        queue_repo.update_ticket(db, ticket, "cancelled", actor_user_id=actor_id, note=payload.reason)
    audit_repo.log(
        db,
        action="request.cancel",
        entity_type="care_request",
        entity_id=request.id,
        actor_user_id=actor_id,
        details={"reason": payload.reason},
    )
    out = _to_out(db, request)
    publish_event(
        channel_for_request(request.id),
        event_message("request_status", out.model_dump(mode="json")),
    )
    return out


def timeline(db: Session, request_id: str, user_id: Optional[str], is_admin: bool = False) -> List[RequestEventOut]:
    request = request_repo.get_request(db, request_id)
    if not request:
        raise NotFoundError("Solicitação não encontrada")
    if not can_access(db, request, user_id, is_admin):
        raise ForbiddenError("Acesso negado")
    return [
        RequestEventOut.model_validate(e) for e in request_repo.list_events(db, request_id)
    ]


def set_risk_classification(
    db: Session,
    request_id: str,
    payload: RiskClassificationIn,
    actor_id: Optional[str],
) -> RequestOut:
    request = request_repo.get_request(db, request_id)
    if not request:
        raise NotFoundError("Solicitação não encontrada")
    request.risk_classification = payload.risk_classification
    db.commit()
    request_repo.add_event(
        db,
        request_id,
        "risk_classified",
        actor_user_id=actor_id,
        note=payload.notes or f"Classificação: {payload.risk_classification}",
    )
    audit_repo.log(
        db,
        action="request.risk_classified",
        entity_type="care_request",
        entity_id=request.id,
        actor_user_id=actor_id,
        details={
            "risk": payload.risk_classification,
            "protocol": payload.classification_protocol,
        },
    )
    return _to_out(db, request)


def can_access(db: Session, request: CareRequest, user_id: Optional[str], is_admin: bool) -> bool:
    if is_admin:
        return True
    if request.patient_user_id and request.patient_user_id == user_id:
        return True
    if user_id:
        unit_ids = user_repo.get_user_unit_ids(db, user_id)
        return request.unit_id in unit_ids
    return False
