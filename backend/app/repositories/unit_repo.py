from typing import List, Optional

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.exceptions import ConflictError, NotFoundError
from app.models.unit import (
    CapacitySnapshot,
    HealthcareUnit,
    HealthcareUnitService,
)
from app.repositories.base import get_or_404, paged
from app.utils import new_uuid


def get_unit(db: Session, unit_id: str) -> Optional[HealthcareUnit]:
    return db.get(HealthcareUnit, unit_id)


def get_by_cnes(db: Session, cnes_code: str) -> Optional[HealthcareUnit]:
    return db.scalar(select(HealthcareUnit).filter_by(cnes_code=cnes_code))


def list_units(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    unit_type: Optional[str] = None,
    city: Optional[str] = None,
    state: Optional[str] = None,
    q: Optional[str] = None,
    active_only: bool = True,
):
    query = select(HealthcareUnit).filter(HealthcareUnit.deleted_at.is_(None))
    if active_only:
        query = query.filter(HealthcareUnit.is_active.is_(True))
    if unit_type:
        query = query.filter(HealthcareUnit.type == unit_type)
    if city:
        query = query.filter(HealthcareUnit.city.ilike(city))
    if state:
        query = query.filter(HealthcareUnit.state == state.upper())
    if q:
        query = query.filter(HealthcareUnit.name.ilike(f"%{q}%"))
    query = query.order_by(HealthcareUnit.name)
    return paged(db, query, page, page_size)


def create_unit(db: Session, data: dict, services: Optional[list] = None) -> HealthcareUnit:
    if data.get("cnes_code") and get_by_cnes(db, data["cnes_code"]):
        raise ConflictError("Código CNES já cadastrado", code="cnes_exists")
    unit = HealthcareUnit(**{k: v for k, v in data.items() if k != "services"})
    db.add(unit)
    db.flush()
    for svc in services or []:
        db.add(
            HealthcareUnitService(
                unit_id=unit.id,
                service_code=svc["service_code"],
                service_name=svc["service_name"],
                is_available=svc.get("is_available", True),
                notes=svc.get("notes"),
            )
        )
    db.commit()
    db.refresh(unit)
    return unit


def update_unit(db: Session, unit: HealthcareUnit, data: dict) -> HealthcareUnit:
    for field, value in data.items():
        if value is not None and field != "services":
            setattr(unit, field, value)
    db.commit()
    db.refresh(unit)
    return unit


def set_active(db: Session, unit: HealthcareUnit, is_active: bool) -> HealthcareUnit:
    unit.is_active = is_active
    db.commit()
    db.refresh(unit)
    return unit


def soft_delete_unit(db: Session, unit: HealthcareUnit) -> None:
    from datetime import datetime, timezone

    unit.deleted_at = datetime.now(timezone.utc)
    unit.is_active = False
    db.commit()


def list_services(db: Session, unit_id: str) -> List[HealthcareUnitService]:
    return db.scalars(
        select(HealthcareUnitService)
        .filter_by(unit_id=unit_id)
        .order_by(HealthcareUnitService.service_name)
    ).all()


def replace_services(db: Session, unit_id: str, services: List[dict]) -> None:
    db.query(HealthcareUnitService).filter_by(unit_id=unit_id).delete()
    for svc in services:
        db.add(
            HealthcareUnitService(
                unit_id=unit_id,
                service_code=svc["service_code"],
                service_name=svc["service_name"],
                is_available=svc.get("is_available", True),
            )
        )
    db.commit()


def latest_capacity(db: Session, unit_id: str) -> Optional[CapacitySnapshot]:
    return db.scalar(
        select(CapacitySnapshot)
        .filter_by(unit_id=unit_id)
        .order_by(CapacitySnapshot.created_at.desc())
        .limit(1)
    )


def list_capacity(db: Session, unit_id: str, limit: int = 50) -> List[CapacitySnapshot]:
    return db.scalars(
        select(CapacitySnapshot)
        .filter_by(unit_id=unit_id)
        .order_by(CapacitySnapshot.created_at.desc())
        .limit(limit)
    ).all()


def add_capacity(db: Session, unit_id: str, data: dict, created_by: Optional[str]) -> CapacitySnapshot:
    from datetime import datetime, timezone

    snapshot = CapacitySnapshot(
        unit_id=unit_id,
        professionals_available=data.get("professionals_available", 0),
        rooms_active=data.get("rooms_active", 0),
        welcome_capacity=data.get("welcome_capacity", 0),
        services_unavailable=data.get("services_unavailable") or [],
        receiving_pre_registrations=data.get("receiving_pre_registrations", True),
        exceptional_status=data.get("exceptional_status"),
        notes=data.get("notes"),
        created_by=created_by,
        # created_at explícito com microssegundos: o servidor SQLite tem precisão de segundo
        created_at=datetime.now(timezone.utc),
    )
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    return snapshot


def default_capacity() -> dict:
    return {
        "professionals_available": 0,
        "rooms_active": 0,
        "welcome_capacity": 0,
        "services_unavailable": [],
        "receiving_pre_registrations": True,
        "exceptional_status": None,
    }


def count_by_type(db: Session) -> dict:
    rows = db.execute(
        select(HealthcareUnit.type, func.count(HealthcareUnit.id))
        .filter(HealthcareUnit.deleted_at.is_(None))
        .group_by(HealthcareUnit.type)
    ).all()
    return {row[0]: row[1] for row in rows}
