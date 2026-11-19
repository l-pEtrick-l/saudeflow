from typing import Optional

from sqlalchemy.orm import Session

from app.models.estimate import WaitEstimate
from app.repositories import estimate_repo, queue_repo, request_repo, unit_repo
from app.schemas.estimate import EstimateOut
from app.services import unit_service


def compute_and_cache(db: Session, unit_id: str) -> EstimateOut:
    """Recalcula a estimativa da unidade e persiste o cache."""
    from app.services.guidance_engine import compute_wait_estimate

    durations = queue_repo.recent_durations(db, unit_id, days=30)
    waiting = (
        db_count_waiting(db, unit_id)
    )
    capacity = unit_service.current_capacity(db, unit_id)
    computed = compute_wait_estimate(
        durations=durations,
        waiting_count=waiting,
        professionals_available=capacity.get("professionals_available", 0),
    )
    row = estimate_repo.upsert(
        db,
        unit_id,
        {
            "low_minutes": computed["low_minutes"],
            "p50_minutes": computed["p50_minutes"],
            "high_minutes": computed["high_minutes"],
            "sample_size": computed["sample_size"],
            "method": computed["method"],
            "is_reliable": computed["is_reliable"],
        },
    )
    return EstimateOut(
        unit_id=unit_id,
        is_reliable=row.is_reliable,
        low_minutes=row.low_minutes,
        p50_minutes=row.p50_minutes,
        high_minutes=row.high_minutes,
        sample_size=row.sample_size,
        method=row.method,
        message=computed["message"],
        computed_at=row.computed_at,
    )


def db_count_waiting(db: Session, unit_id: str) -> int:
    """Pessoas aguardando na fila digital (etapa administrativa, não clínica)."""
    return _waiting_tickets(db, unit_id)


def _waiting_tickets(db: Session, unit_id: str) -> int:
    return (
        db.query(queue_repo.QueueTicket)
        .filter(queue_repo.QueueTicket.unit_id == unit_id)
        .filter(queue_repo.QueueTicket.status == "waiting")
        .count()
    )


def get_estimate(db: Session, unit_id: str, recompute: bool = False) -> EstimateOut:
    if recompute:
        return compute_and_cache(db, unit_id)
    row = estimate_repo.get(db, unit_id)
    if row is None:
        return compute_and_cache(db, unit_id)
    message = _message_for(row, db, unit_id)
    return EstimateOut(
        unit_id=unit_id,
        is_reliable=row.is_reliable,
        low_minutes=row.low_minutes,
        p50_minutes=row.p50_minutes,
        high_minutes=row.high_minutes,
        sample_size=row.sample_size,
        method=row.method,
        message=message,
        computed_at=row.computed_at,
    )


def _message_for(row: WaitEstimate, db: Session, unit_id: str) -> str:
    if row.is_reliable:
        return (
            f"Espera estimada: {int(row.low_minutes or 0)}–{int(row.high_minutes or 0)} minutos. "
            "Estimativa operacional, não garantia de atendimento."
        )
    return (
        "Não há dados suficientes para estimar a espera desta unidade. "
        "A estimativa só é exibida quando há histórico mínimo de atendimentos."
    )
