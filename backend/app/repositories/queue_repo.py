from datetime import datetime, timedelta, timezone
from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.exceptions import ConflictError
from app.models.queue import Attendance, CheckIn, QueueEvent, QueueTicket
from app.repositories.base import get_or_404

TICKET_STATUSES = ["waiting", "called", "attending", "done", "cancelled", "absent"]


def create_ticket(db: Session, request_id: str, unit_id: str) -> QueueTicket:
    position = (
        db.scalar(
            select(func.count(QueueTicket.id)).filter_by(unit_id=unit_id, status="waiting")
        )
        or 0
    ) + 1
    ticket = QueueTicket(
        request_id=request_id, unit_id=unit_id, position=position, status="waiting"
    )
    db.add(ticket)
    db.flush()
    db.add(
        QueueEvent(
            ticket_id=ticket.id,
            event_type="created",
            to_status="waiting",
            note="Pré-cadastro recebido",
        )
    )
    db.commit()
    db.refresh(ticket)
    return ticket


def get_ticket(db: Session, ticket_id: str) -> Optional[QueueTicket]:
    return db.get(QueueTicket, ticket_id)


def get_ticket_for_request(db: Session, request_id: str) -> Optional[QueueTicket]:
    return db.scalar(select(QueueTicket).filter_by(request_id=request_id))


def list_tickets(
    db: Session, unit_id: str, status: Optional[str] = None
) -> List[QueueTicket]:
    query = select(QueueTicket).filter_by(unit_id=unit_id)
    if status:
        query = query.filter_by(status=status)
    return db.scalars(query.order_by(QueueTicket.position, QueueTicket.created_at)).all()


def next_waiting(db: Session, unit_id: str) -> Optional[QueueTicket]:
    return db.scalar(
        select(QueueTicket)
        .filter_by(unit_id=unit_id, status="waiting")
        .order_by(QueueTicket.position, QueueTicket.created_at)
        .limit(1)
    )


def update_ticket(
    db: Session,
    ticket: QueueTicket,
    status: str,
    actor_user_id: Optional[str] = None,
    note: Optional[str] = None,
    position: Optional[int] = None,
) -> QueueTicket:
    if status not in TICKET_STATUSES:
        raise ConflictError(f"Status de ticket inválido: {status}", code="invalid_ticket_status")
    previous = ticket.status
    ticket.status = status
    if position is not None:
        ticket.position = position
    db.add(
        QueueEvent(
            ticket_id=ticket.id,
            event_type="status_change",
            from_status=previous,
            to_status=status,
            actor_user_id=actor_user_id,
            note=note,
        )
    )
    db.commit()
    db.refresh(ticket)
    return ticket


def add_event(
    db: Session,
    ticket_id: str,
    event_type: str,
    actor_user_id: Optional[str] = None,
    note: Optional[str] = None,
) -> QueueEvent:
    event = QueueEvent(
        ticket_id=ticket_id, event_type=event_type, actor_user_id=actor_user_id, note=note
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def create_checkin(db: Session, request_id: str, unit_id: str, method: str, operator_id: Optional[str]) -> CheckIn:
    checkin = CheckIn(
        request_id=request_id, unit_id=unit_id, method=method, operator_id=operator_id
    )
    db.add(checkin)
    db.commit()
    db.refresh(checkin)
    return checkin


def create_attendance(
    db: Session,
    request_id: str,
    unit_id: str,
    started_at: datetime,
    professional_id: Optional[str] = None,
) -> Attendance:
    attendance = Attendance(
        request_id=request_id,
        unit_id=unit_id,
        started_at=started_at,
        professional_id=professional_id,
    )
    db.add(attendance)
    db.commit()
    db.refresh(attendance)
    return attendance


def finish_attendance(
    db: Session,
    attendance: Attendance,
    finished_at: datetime,
    outcome: Optional[str] = None,
    risk_classification: Optional[str] = None,
    classification_protocol: Optional[str] = None,
    notes: Optional[str] = None,
) -> Attendance:
    attendance.finished_at = finished_at
    start = attendance.started_at
    if start.tzinfo is not None:
        start = start.astimezone(timezone.utc).replace(tzinfo=None)
    end = finished_at
    if end.tzinfo is not None:
        end = end.astimezone(timezone.utc).replace(tzinfo=None)
    attendance.duration_minutes = max(1, int((end - start).total_seconds() / 60))
    attendance.outcome = outcome
    attendance.risk_classification = risk_classification
    attendance.classification_protocol = classification_protocol
    attendance.notes = notes
    db.commit()
    db.refresh(attendance)
    return attendance


def recent_durations(db: Session, unit_id: str, days: int = 30, limit: int = 500) -> List[float]:
    since = datetime.now(timezone.utc) - timedelta(days=days)
    rows = db.execute(
        select(Attendance.duration_minutes).filter(
            Attendance.unit_id == unit_id,
            Attendance.duration_minutes.isnot(None),
            Attendance.started_at >= since,
        ).limit(limit)
    ).all()
    return [float(r[0]) for r in rows]


def list_attendances(db: Session, unit_id: str, limit: int = 50) -> List[Attendance]:
    return db.scalars(
        select(Attendance)
        .filter_by(unit_id=unit_id)
        .order_by(Attendance.started_at.desc())
        .limit(limit)
    ).all()


def average_duration(db: Session, unit_id: str) -> Optional[float]:
    value = db.scalar(
        select(func.avg(Attendance.duration_minutes)).filter(
            Attendance.unit_id == unit_id,
            Attendance.duration_minutes.isnot(None),
        )
    )
    return float(value) if value else None
