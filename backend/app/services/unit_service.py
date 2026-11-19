from typing import List, Optional

from sqlalchemy.orm import Session

from app.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.models.unit import CapacitySnapshot, HealthcareUnit
from app.repositories import estimate_repo, request_repo, unit_repo
from app.schemas.unit import (
    CapacityOut,
    CapacityIn,
    UnitCreate,
    UnitOut,
    UnitUpdate,
)
from app.services import estimate_service


def _enrich(db: Session, unit: HealthcareUnit, lat: Optional[float], lon: Optional[float]) -> UnitOut:
    from app.utils import haversine_km

    services = unit_repo.list_services(db, unit.id)
    estimate = estimate_service.get_estimate(db, unit.id)
    distance = None
    if lat is not None and lon is not None and unit.latitude is not None and unit.longitude is not None:
        distance = round(haversine_km(lat, lon, unit.latitude, unit.longitude), 2)
    return UnitOut(
        id=unit.id,
        name=unit.name,
        type=unit.type,
        cnes_code=unit.cnes_code,
        source=unit.source,
        is_simulated=unit.is_simulated,
        is_active=unit.is_active,
        street=unit.street,
        number=unit.number,
        complement=unit.complement,
        neighborhood=unit.neighborhood,
        city=unit.city,
        state=unit.state,
        postal_code=unit.postal_code,
        latitude=unit.latitude,
        longitude=unit.longitude,
        phone=unit.phone,
        email=unit.email,
        services=[
            {
                "id": s.id,
                "unit_id": s.unit_id,
                "service_code": s.service_code,
                "service_name": s.service_name,
                "is_available": s.is_available,
                "notes": s.notes,
            }
            for s in services
        ],
        distance_km=distance,
        estimate={
            "is_reliable": estimate.is_reliable,
            "low_minutes": estimate.low_minutes,
            "p50_minutes": estimate.p50_minutes,
            "high_minutes": estimate.high_minutes,
            "message": estimate.message,
            "updated_at": estimate.computed_at,
        },
        digital_queue_count=request_repo.count_digital_queue(db, unit.id),
        updated_at=unit.updated_at,
    )


def list_public_units(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    unit_type: Optional[str] = None,
    city: Optional[str] = None,
    state: Optional[str] = None,
    q: Optional[str] = None,
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    include_external: bool = False,
):
    items, total = unit_repo.list_units(
        db, page, page_size, unit_type, city, state, q, active_only=True
    )
    return [_enrich(db, u, lat, lon) for u in items], total


def get_unit(db: Session, unit_id: str, lat=None, lon=None) -> UnitOut:
    unit = unit_repo.get_unit(db, unit_id)
    if not unit:
        raise NotFoundError("Unidade não encontrada")
    return _enrich(db, unit, lat, lon)


def create_unit(db: Session, payload: UnitCreate) -> UnitOut:
    unit = unit_repo.create_unit(db, payload.model_dump(), payload.services)
    return get_unit(db, unit.id)


def update_unit(db: Session, unit_id: str, payload: UnitUpdate) -> UnitOut:
    unit = unit_repo.get_unit(db, unit_id)
    if not unit:
        raise NotFoundError("Unidade não encontrada")
    unit_repo.update_unit(db, unit, payload.model_dump(exclude_none=True))
    return get_unit(db, unit.id)


def set_active(db: Session, unit_id: str, is_active: bool) -> UnitOut:
    unit = unit_repo.get_unit(db, unit_id)
    if not unit:
        raise NotFoundError("Unidade não encontrada")
    unit_repo.set_active(db, unit, is_active)
    return get_unit(db, unit.id)


def list_capacity(db: Session, unit_id: str) -> List[CapacityOut]:
    if not unit_repo.get_unit(db, unit_id):
        raise NotFoundError("Unidade não encontrada")
    return [
        CapacityOut.model_validate(s) for s in unit_repo.list_capacity(db, unit_id)
    ]


def current_capacity(db: Session, unit_id: str) -> dict:
    snapshot = unit_repo.latest_capacity(db, unit_id)
    if snapshot is None:
        return unit_repo.default_capacity()
    return {
        "professionals_available": snapshot.professionals_available,
        "rooms_active": snapshot.rooms_active,
        "welcome_capacity": snapshot.welcome_capacity,
        "services_unavailable": snapshot.services_unavailable or [],
        "receiving_pre_registrations": snapshot.receiving_pre_registrations,
        "exceptional_status": snapshot.exceptional_status,
    }


def update_capacity(
    db: Session, unit_id: str, payload: CapacityIn, actor_id: Optional[str]
) -> CapacityOut:
    unit = unit_repo.get_unit(db, unit_id)
    if not unit:
        raise NotFoundError("Unidade não encontrada")
    snapshot = unit_repo.add_capacity(db, unit_id, payload.model_dump(), actor_id)
    estimate_service.compute_and_cache(db, unit_id)
    from app.realtime import channel_for_unit, event_message, publish_event

    publish_event(
        channel_for_unit(unit_id),
        event_message("capacity_updated", {"unit_id": unit_id}),
    )
    return CapacityOut.model_validate(snapshot)
