from datetime import datetime, timedelta, timezone
from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.alert import EmergencyAlert, EmergencyAlertEvent
from app.repositories.base import paged

ALERT_STATUSES = ["new", "received", "confirmed", "arrived", "closed", "cancelled"]

ALERT_STATUS_LABELS = {
    "new": "Novo alerta",
    "received": "Recebido",
    "confirmed": "Confirmado pela equipe",
    "arrived": "Chegada registrada",
    "closed": "Encerrado",
    "cancelled": "Cancelado",
}


def create_alert(db: Session, data: dict) -> EmergencyAlert:
    alert = EmergencyAlert(**data)
    db.add(alert)
    db.flush()
    db.add(
        EmergencyAlertEvent(
            alert_id=alert.id,
            event_type="created",
            note="Pré-alerta criado pelo portal do paciente",
        )
    )
    db.commit()
    db.refresh(alert)
    return alert


def get_alert(db: Session, alert_id: str) -> Optional[EmergencyAlert]:
    return db.get(EmergencyAlert, alert_id)


def get_by_code(db: Session, code: str) -> Optional[EmergencyAlert]:
    return db.scalar(select(EmergencyAlert).filter_by(alert_code=code))


def list_alerts(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    unit_id: Optional[str] = None,
    status: Optional[str] = None,
    reporter_user_id: Optional[str] = None,
):
    query = select(EmergencyAlert)
    if unit_id:
        query = query.filter_by(destination_unit_id=unit_id)
    if status:
        query = query.filter_by(status=status)
    if reporter_user_id:
        query = query.filter_by(reporter_user_id=reporter_user_id)
    query = query.order_by(EmergencyAlert.created_at.desc())
    return paged(db, query, page, page_size)


def update_alert(
    db: Session,
    alert: EmergencyAlert,
    status: str,
    actor_user_id: Optional[str] = None,
    note: Optional[str] = None,
) -> EmergencyAlert:
    if status not in ALERT_STATUSES:
        raise ValueError(f"Status inválido: {status}")
    previous = alert.status
    alert.status = status
    db.add(
        EmergencyAlertEvent(
            alert_id=alert.id,
            event_type="status_change",
            note=note or f"{previous} → {status}",
            actor_user_id=actor_user_id,
        )
    )
    db.commit()
    db.refresh(alert)
    return alert


def list_events(db: Session, alert_id: str) -> List[EmergencyAlertEvent]:
    return db.scalars(
        select(EmergencyAlertEvent)
        .filter_by(alert_id=alert_id)
        .order_by(EmergencyAlertEvent.created_at, EmergencyAlertEvent.id)
    ).all()


def count_by_status(db: Session, unit_id: Optional[str] = None) -> dict:
    query = select(EmergencyAlert.status, func.count(EmergencyAlert.id))
    if unit_id:
        query = query.filter_by(destination_unit_id=unit_id)
    rows = db.execute(query.group_by(EmergencyAlert.status)).all()
    return {row[0]: row[1] for row in rows}


def active_on_the_way(db: Session, unit_id: str) -> int:
    return db.scalar(
        select(func.count(EmergencyAlert.id)).filter(
            EmergencyAlert.destination_unit_id == unit_id,
            EmergencyAlert.status.in_(["new", "received", "confirmed"]),
        )
    ) or 0


def average_confirmation_minutes(db: Session, unit_id: str) -> Optional[float]:
    """Tempo médio entre criação e confirmação (evento 'confirmed')."""
    rows = db.execute(
        select(
            EmergencyAlert.id,
            EmergencyAlert.created_at,
        ).filter(
            EmergencyAlert.destination_unit_id == unit_id,
            EmergencyAlert.status.in_(["confirmed", "arrived", "closed"]),
        )
    ).all()
    if not rows:
        return None
    diffs = []
    for alert_id, created_at in rows:
        confirmed = db.scalar(
            select(EmergencyAlertEvent.created_at)
            .filter_by(alert_id=alert_id, event_type="status_change")
            .order_by(EmergencyAlertEvent.created_at)
        )
        if confirmed and created_at:
            diffs.append(abs((confirmed - created_at).total_seconds()) / 60.0)
    return sum(diffs) / len(diffs) if diffs else None


def alerts_by_day(db: Session, unit_id: Optional[str] = None, days: int = 14) -> List[dict]:
    since = datetime.now(timezone.utc) - timedelta(days=days)
    query = select(
        func.date(EmergencyAlert.created_at), func.count(EmergencyAlert.id)
    ).filter(EmergencyAlert.created_at >= since)
    if unit_id:
        query = query.filter_by(destination_unit_id=unit_id)
    rows = db.execute(query.group_by(func.date(EmergencyAlert.created_at))).all()
    return [{"date": str(r[0]), "count": r[1]} for r in rows]
