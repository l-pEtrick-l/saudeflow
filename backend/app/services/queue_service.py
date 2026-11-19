from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.orm import Session

from app.exceptions import ConflictError, NotFoundError, UnprocessableError
from app.models.queue import QueueTicket
from app.repositories import (
    audit_repo,
    notification_repo,
    queue_repo,
    request_repo,
    unit_repo,
)
from app.realtime import (
    channel_for_request,
    channel_for_unit,
    channel_for_user,
    event_message,
    publish_event,
)
from app.schemas.queue import CallNextOut, QueueBoardOut, QueueTicketOut
from app.services import estimate_service, request_service, unit_service


def _ticket_out(db: Session, ticket: QueueTicket) -> QueueTicketOut:
    request = request_repo.get_request(db, ticket.request_id)
    return QueueTicketOut(
        id=ticket.id,
        request_id=ticket.request_id,
        unit_id=ticket.unit_id,
        position=ticket.position,
        status=ticket.status,
        protocol=request.protocol if request else None,
        patient_name=request.patient_name if request else None,
        category=request.category if request else None,
        complaint_summary=request.complaint_summary if request else None,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
    )


def board(db: Session, unit_id: str) -> QueueBoardOut:
    if not unit_repo.get_unit(db, unit_id):
        raise NotFoundError("Unidade não encontrada")
    tickets = [
        t
        for t in queue_repo.list_tickets(db, unit_id)
        if t.status in ("waiting", "called", "attending")
    ]
    estimate = estimate_service.get_estimate(db, unit_id)
    return QueueBoardOut(
        unit_id=unit_id,
        unit_name=unit_repo.get_unit(db, unit_id).name,
        capacity=unit_service.current_capacity(db, unit_id),
        estimate={
            "is_reliable": estimate.is_reliable,
            "low_minutes": estimate.low_minutes,
            "p50_minutes": estimate.p50_minutes,
            "high_minutes": estimate.high_minutes,
            "message": estimate.message,
            "updated_at": estimate.computed_at,
        },
        tickets=[_ticket_out(db, t) for t in tickets],
    )


def call_next(db: Session, unit_id: str, actor_id: Optional[str]) -> CallNextOut:
    ticket = queue_repo.next_waiting(db, unit_id)
    if not ticket:
        return CallNextOut(called=None, message="Não há solicitações aguardando.")
    queue_repo.update_ticket(
        db, ticket, "called", actor_user_id=actor_id, note="Protocolo chamado"
    )
    request = request_repo.get_request(db, ticket.request_id)
    if request and request.status in ("sent", "awaiting_confirmation", "pre_register_confirmed"):
        request_service.update_status(
            db,
            request.id,
            "awaiting_welcome",
            actor_id,
            "Protocolo chamado pela unidade",
        )
    else:
        db.refresh(ticket)
    out = _ticket_out(db, ticket)
    publish_event(
        channel_for_unit(unit_id),
        event_message("queue_updated", {"unit_id": unit_id, "ticket_id": ticket.id}),
    )
    return CallNextOut(called=out, message=f"Protocolo {out.protocol} chamado.")


def checkin(
    db: Session,
    request_id: str,
    unit_id: str,
    actor_id: Optional[str],
    method: str = "desk",
):
    request = request_repo.get_request(db, request_id)
    if not request:
        raise NotFoundError("Solicitação não encontrada")
    if request.unit_id != unit_id:
        raise UnprocessableError("Solicitação não pertence a esta unidade")
    queue_repo.create_checkin(db, request_id, unit_id, method, actor_id)
    return request_service.update_status(
        db, request_id, "patient_arrived", actor_id, "Chegada registrada"
    )


def start_care(db: Session, request_id: str, actor_id: Optional[str], professional_id: Optional[str] = None):
    request = request_repo.get_request(db, request_id)
    if not request:
        raise NotFoundError("Solicitação não encontrada")
    queue_repo.create_attendance(
        db, request_id, request.unit_id, datetime.now(timezone.utc), professional_id
    )
    return request_service.update_status(
        db, request_id, "in_care", actor_id, "Atendimento iniciado"
    )


def finish_care(
    db: Session,
    request_id: str,
    actor_id: Optional[str],
    outcome: Optional[str] = None,
    risk_classification: Optional[str] = None,
    classification_protocol: Optional[str] = None,
    notes: Optional[str] = None,
):
    request = request_repo.get_request(db, request_id)
    if not request:
        raise NotFoundError("Solicitação não encontrada")
    attendance = (
        db.query(queue_repo.Attendance)
        .filter_by(request_id=request_id, finished_at=None)
        .order_by(queue_repo.Attendance.started_at.desc())
        .first()
    )
    if attendance:
        queue_repo.finish_attendance(
            db,
            attendance,
            datetime.now(timezone.utc),
            outcome=outcome,
            risk_classification=risk_classification,
            classification_protocol=classification_protocol,
            notes=notes,
        )
    estimate_service.compute_and_cache(db, request.unit_id)
    return request_service.update_status(
        db, request_id, "finished", actor_id, "Atendimento finalizado"
    )


def list_attendances(db: Session, unit_id: str, limit: int = 50):
    return queue_repo.list_attendances(db, unit_id, limit)


def confirm_receipt(db: Session, request_id: str, actor_id: Optional[str]):
    request = request_repo.get_request(db, request_id)
    if not request:
        raise NotFoundError("Solicitação não encontrada")
    if request.status not in ("sent", "awaiting_confirmation"):
        raise ConflictError("Solicitação já está em andamento", code="invalid_transition")
    return request_service.update_status(
        db, request_id, "pre_register_confirmed", actor_id, "Pré-cadastro confirmado"
    )
