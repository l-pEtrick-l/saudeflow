from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.alert import EmergencyAlert
from app.models.queue import Attendance
from app.models.request import CareRequest
from app.models.unit import HealthcareUnit
from app.models.user import User
from app.repositories import alert_repo, queue_repo, request_repo, unit_repo
from app.schemas.analytics import HospitalStatsOut, OverviewOut, UnitStatsOut
from app.services import estimate_service, unit_service


def overview(db: Session) -> OverviewOut:
    total_units = db.scalar(
        select(func.count(HealthcareUnit.id)).filter(HealthcareUnit.deleted_at.is_(None))
    ) or 0
    total_users = db.scalar(
        select(func.count(User.id)).filter(User.deleted_at.is_(None))
    ) or 0
    requests_by_status = request_repo.count_by_status(db)
    alerts_by_status = alert_repo.count_by_status(db)
    avg = queue_repo.average_duration(db, None) if False else _global_avg_duration(db)
    return OverviewOut(
        total_units=total_units,
        units_by_type=unit_repo.count_by_type(db),
        total_users=total_users,
        total_requests=sum(requests_by_status.values()),
        requests_by_status=requests_by_status,
        active_requests=sum(
            v
            for k, v in requests_by_status.items()
            if k not in ("finished", "cancelled")
        ),
        total_alerts=sum(alerts_by_status.values()),
        alerts_by_status=alerts_by_status,
        average_attendance_minutes=round(avg, 1) if avg else None,
        last_24h_requests=request_repo.last_24h_requests(db),
    )


def _global_avg_duration(db: Session) -> Optional[float]:
    value = db.scalar(select(func.avg(Attendance.duration_minutes)).filter(
        Attendance.duration_minutes.isnot(None)
    ))
    return float(value) if value else None


def unit_stats(db: Session, unit_id: str) -> UnitStatsOut:
    unit = unit_repo.get_unit(db, unit_id)
    if not unit:
        from app.exceptions import NotFoundError

        raise NotFoundError("Unidade não encontrada")
    by_status = request_repo.count_by_status(db, unit_id)
    estimate = estimate_service.get_estimate(db, unit_id)
    avg_wait = db.scalar(
        select(func.avg(Attendance.duration_minutes)).filter(
            Attendance.unit_id == unit_id,
            Attendance.duration_minutes.isnot(None),
        )
    )
    alerts = alert_repo.count_by_status(db, unit_id)
    return UnitStatsOut(
        unit_id=unit_id,
        unit_name=unit.name,
        requests_received=sum(by_status.values()),
        pre_registers_confirmed=by_status.get("pre_register_confirmed", 0),
        patients_present=by_status.get("patient_arrived", 0),
        awaiting_welcome=by_status.get("awaiting_welcome", 0),
        in_care=by_status.get("in_care", 0),
        finished=by_status.get("finished", 0),
        cancelled=by_status.get("cancelled", 0),
        average_wait_minutes=round(float(avg_wait), 1) if avg_wait else None,
        capacity=unit_service.current_capacity(db, unit_id),
        estimate={
            "is_reliable": estimate.is_reliable,
            "low_minutes": estimate.low_minutes,
            "high_minutes": estimate.high_minutes,
            "message": estimate.message,
        },
        alerts_received=sum(alerts.values()),
        average_confirmation_minutes=alert_repo.average_confirmation_minutes(db, unit_id),
        by_day=_requests_by_day(db, unit_id),
    )


def hospital_stats(db: Session, unit_id: str) -> HospitalStatsOut:
    unit = unit_repo.get_unit(db, unit_id)
    if not unit:
        from app.exceptions import NotFoundError

        raise NotFoundError("Unidade não encontrada")
    by_status = alert_repo.count_by_status(db, unit_id)
    return HospitalStatsOut(
        unit_id=unit_id,
        unit_name=unit.name,
        alerts_total=sum(by_status.values()),
        alerts_by_status=by_status,
        patients_on_the_way=alert_repo.active_on_the_way(db, unit_id),
        average_confirmation_minutes=alert_repo.average_confirmation_minutes(db, unit_id),
        by_day=alert_repo.alerts_by_day(db, unit_id),
        by_city=_alerts_by_city(db, unit_id),
    )


def _requests_by_day(db: Session, unit_id: str, days: int = 14):
    since = datetime.now(timezone.utc) - timedelta(days=days)
    rows = db.execute(
        select(func.date(CareRequest.created_at), func.count(CareRequest.id))
        .filter(CareRequest.unit_id == unit_id, CareRequest.created_at >= since)
        .group_by(func.date(CareRequest.created_at))
    ).all()
    return [{"date": str(r[0]), "count": r[1]} for r in rows]


def _alerts_by_city(db: Session, unit_id: str):
    unit = unit_repo.get_unit(db, unit_id)
    if not unit or not unit.city:
        return []
    return [{"city": unit.city, "count": alert_repo.count_by_status(db, unit_id).get("new", 0) + sum(alert_repo.count_by_status(db, unit_id).values())}]
