from datetime import datetime, timezone
from typing import List, Optional
from uuid import uuid4

from sqlalchemy.orm import Session

from app.exceptions import ForbiddenError, NotFoundError, UnprocessableError
from app.models.alert import EmergencyAlert
from app.repositories import (
    alert_repo,
    audit_repo,
    notification_repo,
    unit_repo,
    user_repo,
)
from app.realtime import (
    channel_for_alert,
    channel_for_unit,
    channel_for_user,
    event_message,
    publish_event,
)
from app.schemas.alert import AlertCreate, AlertOut, AlertUpdate


def _to_out(db: Session, alert: EmergencyAlert) -> AlertOut:
    unit = unit_repo.get_unit(db, alert.destination_unit_id)
    return AlertOut(
        id=alert.id,
        alert_code=alert.alert_code,
        destination_unit_id=alert.destination_unit_id,
        destination_unit_name=unit.name if unit else None,
        description=alert.description,
        occurred_at=alert.occurred_at,
        patient_conscious=alert.patient_conscious,
        patient_breathing=alert.patient_breathing,
        bleeding=alert.bleeding,
        current_situation=alert.current_situation,
        eta_minutes=alert.eta_minutes,
        alert_flags=alert.alert_flags or [],
        status=alert.status,
        status_label=alert_repo.ALERT_STATUS_LABELS.get(alert.status, alert.status),
        created_at=alert.created_at,
        updated_at=alert.updated_at,
        events=[
            {
                "id": e.id,
                "event_type": e.event_type,
                "note": e.note,
                "actor_user_id": e.actor_user_id,
                "created_at": e.created_at,
            }
            for e in alert_repo.list_events(db, alert.id)
        ],
    )


def _alert_flags(payload: AlertCreate) -> List[str]:
    flags = []
    if payload.patient_conscious == "no":
        flags.append("loss_of_consciousness")
    if payload.patient_breathing == "no":
        flags.append("respiratory_emergency")
    if payload.bleeding == "yes":
        flags.append("severe_bleeding")
    if payload.eta_minutes is not None:
        flags.append("patient_on_the_way")
    return sorted(set(flags))


def create_alert(
    db: Session,
    payload: AlertCreate,
    user_id: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> AlertOut:
    unit = unit_repo.get_unit(db, payload.destination_unit_id)
    if not unit or not unit.is_active:
        raise NotFoundError("Unidade de destino não encontrada ou inativa")

    occurred_at = None
    if payload.occurred_at:
        try:
            occurred_at = datetime.fromisoformat(payload.occurred_at.replace("Z", "+00:00"))
        except ValueError:
            raise UnprocessableError("Data/hora de ocorrência inválida", code="invalid_datetime")

    alert = alert_repo.create_alert(
        db,
        {
            "alert_code": f"ALERT-{uuid4().hex[:8].upper()}",
            "reporter_user_id": user_id,
            "destination_unit_id": payload.destination_unit_id,
            "description": payload.description,
            "occurred_at": occurred_at or datetime.now(timezone.utc),
            "patient_conscious": payload.patient_conscious,
            "patient_breathing": payload.patient_breathing,
            "bleeding": payload.bleeding,
            "current_situation": payload.current_situation,
            "eta_minutes": payload.eta_minutes,
            "alert_flags": _alert_flags(payload),
        },
    )
    notification_repo.notify_unit_staff(
        db,
        payload.destination_unit_id,
        "Novo pré-alerta de paciente a caminho",
        payload.description or "Paciente informou que está a caminho da unidade.",
        type="alert",
        alert_id=alert.id,
    )
    if user_id:
        notification_repo.create(
            db,
            title="Pré-alerta enviado",
            body=f"Alerta {alert.alert_code} enviado à unidade. Continue seguindo as orientações de emergência.",
            type="alert",
            user_id=user_id,
            alert_id=alert.id,
        )
    audit_repo.log(
        db,
        action="alert.create",
        entity_type="emergency_alert",
        entity_id=alert.id,
        actor_user_id=user_id,
        details={"alert_code": alert.alert_code, "unit_id": payload.destination_unit_id},
        ip_address=ip_address,
    )
    out = _to_out(db, alert)
    publish_event(channel_for_alert(alert.id), event_message("alert_status", out.model_dump(mode="json")))
    publish_event(
        channel_for_unit(payload.destination_unit_id),
        event_message("alert_received", out.model_dump(mode="json")),
    )
    if user_id:
        publish_event(channel_for_user(user_id), event_message("alert_status", out.model_dump(mode="json")))
    return out


def get_alert(db: Session, alert_id: str, user_id: Optional[str], is_admin: bool = False) -> AlertOut:
    alert = alert_repo.get_alert(db, alert_id)
    if not alert:
        raise NotFoundError("Alerta não encontrado")
    if not _can_access(db, alert, user_id, is_admin):
        raise ForbiddenError("Acesso negado")
    return _to_out(db, alert)


def list_alerts(
    db: Session,
    user_id: str,
    is_admin: bool,
    unit_ids: List[str],
    page: int,
    page_size: int,
    status: Optional[str] = None,
):
    if is_admin:
        items, total = alert_repo.list_alerts(db, page, page_size, status=status)
    elif unit_ids:
        items, total = [], 0
        for uid in unit_ids:
            page_items, _ = alert_repo.list_alerts(db, page=1, page_size=page_size, unit_id=uid, status=status)
            items.extend(page_items)
        items = sorted(items, key=lambda a: a.created_at, reverse=True)
        total = len(items)
        items = items[(page - 1) * page_size : page * page_size]
    else:
        items, total = alert_repo.list_alerts(
            db, page, page_size, reporter_user_id=user_id, status=status
        )
    return [_to_out(db, a) for a in items], total


def update_status(
    db: Session,
    alert_id: str,
    payload: AlertUpdate,
    actor_id: Optional[str],
    is_admin: bool = False,
) -> AlertOut:
    alert = alert_repo.get_alert(db, alert_id)
    if not alert:
        raise NotFoundError("Alerta não encontrado")
    if not is_admin and alert.destination_unit_id not in user_repo.get_user_unit_ids(db, actor_id or ""):
        raise ForbiddenError("Acesso negado")
    alert_repo.update_alert(db, alert, payload.status, actor_id, payload.note)
    audit_repo.log(
        db,
        action="alert.status",
        entity_type="emergency_alert",
        entity_id=alert.id,
        actor_user_id=actor_id,
        details={"to": payload.status},
    )
    out = _to_out(db, alert)
    publish_event(channel_for_alert(alert.id), event_message("alert_status", out.model_dump(mode="json")))
    if alert.reporter_user_id:
        notification_repo.create(
            db,
            title="Atualização do pré-alerta",
            body=f"{alert.alert_code}: {alert_repo.ALERT_STATUS_LABELS.get(payload.status, payload.status)}",
            type="alert",
            user_id=alert.reporter_user_id,
            alert_id=alert.id,
        )
        publish_event(channel_for_user(alert.reporter_user_id), event_message("alert_status", out.model_dump(mode="json")))
    return out


def confirm(db: Session, alert_id: str, actor_id: Optional[str]) -> AlertOut:
    return update_status(db, alert_id, AlertUpdate(status="confirmed", note="Recebimento confirmado"), actor_id)


def _can_access(db: Session, alert: EmergencyAlert, user_id: Optional[str], is_admin: bool) -> bool:
    if is_admin:
        return True
    if alert.reporter_user_id and alert.reporter_user_id == user_id:
        return True
    if user_id:
        return alert.destination_unit_id in user_repo.get_user_unit_ids(db, user_id)
    return False
