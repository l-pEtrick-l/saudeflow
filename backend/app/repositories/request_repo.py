from datetime import datetime
from typing import List, Optional

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.exceptions import ConflictError
from app.models.request import CareRequest, ProtocolCounter, RequestEvent
from app.models.queue import QueueTicket
from app.repositories.base import get_or_404, paged

VALID_STATUSES = [
    "sent",
    "awaiting_confirmation",
    "pre_register_confirmed",
    "patient_arrived",
    "awaiting_welcome",
    "awaiting_care",
    "in_care",
    "finished",
    "cancelled",
]

STATUS_LABELS = {
    "sent": "Solicitação enviada",
    "awaiting_confirmation": "Aguardando confirmação",
    "pre_register_confirmed": "Pré-cadastro confirmado",
    "patient_arrived": "Paciente chegou",
    "awaiting_welcome": "Aguardando acolhimento",
    "awaiting_care": "Aguardando atendimento",
    "in_care": "Em atendimento",
    "finished": "Atendimento finalizado",
    "cancelled": "Cancelado",
}


def next_protocol(db: Session) -> str:
    year = datetime.now().year
    counter = db.get(ProtocolCounter, year)
    if counter is None:
        counter = ProtocolCounter(year=year, seq=0)
        db.add(counter)
        db.flush()
    counter.seq += 1
    db.commit()
    return f"SF-{year}-{counter.seq:06d}"


def create_request(db: Session, data: dict) -> CareRequest:
    payload = dict(data)
    payload["protocol"] = next_protocol(db)
    request = CareRequest(**payload)
    db.add(request)
    db.flush()
    db.add(
        RequestEvent(
            request_id=request.id,
            event_type="status_change",
            to_status=request.status,
            actor_user_id=data.get("patient_user_id"),
            note="Solicitação criada pelo portal do paciente",
        )
    )
    db.commit()
    db.refresh(request)
    from app.repositories import queue_repo

    queue_repo.create_ticket(db, request.id, payload["unit_id"])
    return request


def get_request(db: Session, request_id: str) -> Optional[CareRequest]:
    return db.get(CareRequest, request_id)


def get_by_protocol(db: Session, protocol: str) -> Optional[CareRequest]:
    return db.scalar(select(CareRequest).filter_by(protocol=protocol))


def list_requests(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    unit_id: Optional[str] = None,
    status: Optional[str] = None,
    patient_user_id: Optional[str] = None,
    category: Optional[str] = None,
):
    query = select(CareRequest).filter(CareRequest.deleted_at.is_(None))
    if unit_id:
        query = query.filter_by(unit_id=unit_id)
    if status:
        query = query.filter_by(status=status)
    if patient_user_id:
        query = query.filter_by(patient_user_id=patient_user_id)
    if category:
        query = query.filter_by(category=category)
    query = query.order_by(CareRequest.created_at.desc())
    return paged(db, query, page, page_size)


def update_status(
    db: Session,
    request: CareRequest,
    status: str,
    actor_user_id: Optional[str] = None,
    note: Optional[str] = None,
) -> CareRequest:
    if status not in VALID_STATUSES:
        raise ConflictError(f"Status inválido: {status}", code="invalid_status")
    if status == request.status:
        return request
    previous = request.status
    request.status = status
    db.add(
        RequestEvent(
            request_id=request.id,
            event_type="status_change",
            from_status=previous,
            to_status=status,
            actor_user_id=actor_user_id,
            note=note,
        )
    )
    db.commit()
    db.refresh(request)
    return request


def cancel(db: Session, request: CareRequest, reason: str, actor_user_id: Optional[str]) -> CareRequest:
    previous = request.status
    request.status = "cancelled"
    request.cancellation_reason = reason
    db.add(
        RequestEvent(
            request_id=request.id,
            event_type="cancelled",
            from_status=previous,
            to_status="cancelled",
            actor_user_id=actor_user_id,
            note=reason,
        )
    )
    db.commit()
    db.refresh(request)
    return request


def add_event(
    db: Session,
    request_id: str,
    event_type: str,
    actor_user_id: Optional[str] = None,
    note: Optional[str] = None,
    to_status: Optional[str] = None,
) -> RequestEvent:
    event = RequestEvent(
        request_id=request_id,
        event_type=event_type,
        actor_user_id=actor_user_id,
        note=note,
        to_status=to_status,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def list_events(db: Session, request_id: str) -> List[RequestEvent]:
    return db.scalars(
        select(RequestEvent)
        .filter_by(request_id=request_id)
        .order_by(RequestEvent.created_at, RequestEvent.id)
    ).all()


def count_by_status(db: Session, unit_id: Optional[str] = None) -> dict:
    query = select(CareRequest.status, func.count(CareRequest.id)).filter(
        CareRequest.deleted_at.is_(None)
    )
    if unit_id:
        query = query.filter_by(unit_id=unit_id)
    rows = db.execute(query.group_by(CareRequest.status)).all()
    return {row[0]: row[1] for row in rows}


def active_count(db: Session, unit_id: str) -> int:
    active = ["sent", "awaiting_confirmation", "pre_register_confirmed", "patient_arrived", "awaiting_welcome", "awaiting_care", "in_care"]
    return db.scalar(
        select(func.count(CareRequest.id)).filter(
            CareRequest.unit_id == unit_id,
            CareRequest.deleted_at.is_(None),
            CareRequest.status.in_(active),
        )
    ) or 0


def count_digital_queue(db: Session, unit_id: str) -> int:
    """Solicitações digitais ativas (não representa prioridade clínica)."""
    return db.scalar(
        select(func.count(QueueTicket.id)).filter(
            QueueTicket.unit_id == unit_id,
            QueueTicket.status.in_(["waiting", "called"]),
        )
    ) or 0


def last_24h_requests(db: Session) -> int:
    since = datetime.now() - __import__("datetime").timedelta(hours=24)
    return db.scalar(
        select(func.count(CareRequest.id)).filter(CareRequest.created_at >= since)
    ) or 0
