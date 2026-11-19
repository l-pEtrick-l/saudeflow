from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, get_roles, get_unit_ids, require_roles
from app.exceptions import ForbiddenError
from app.schemas.common import PageMeta
from app.schemas.unit import CapacityIn, CapacityOut, UnitCreate, UnitOut, UnitUpdate
from app.services import estimate_service, unit_service
from app.models.user import User

router = APIRouter(prefix="/units", tags=["Unidades de saúde"])


def _meta(total: int, page: int, page_size: int) -> dict:
    return PageMeta(
        page=page, page_size=page_size, total=total, total_pages=max(1, (total + page_size - 1) // page_size)
    ).model_dump()


def _can_manage(user: User, db: Session, unit_id: str) -> bool:
    if "admin" in get_roles(user, db):
        return True
    return unit_id in get_unit_ids(user, db)


@router.get("")
def list_units(
    unit_type: str | None = Query(None, alias="type"),
    city: str | None = None,
    state: str | None = None,
    q: str | None = None,
    lat: float | None = None,
    lon: float | None = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
):
    items, total = unit_service.list_public_units(
        db, page, page_size, unit_type, city, state, q, lat, lon
    )
    return {"data": items, "meta": _meta(total, page, page_size)}


@router.get("/{unit_id}", response_model=UnitOut)
def get_unit(
    unit_id: str,
    lat: float | None = None,
    lon: float | None = None,
    db: Session = Depends(get_db),
):
    return unit_service.get_unit(db, unit_id, lat, lon)


@router.post("", response_model=UnitOut, status_code=201)
def create_unit(
    payload: UnitCreate,
    db: Session = Depends(get_db),
    _admin=Depends(require_roles("admin")),
):
    return unit_service.create_unit(db, payload)


@router.patch("/{unit_id}", response_model=UnitOut)
def update_unit(
    unit_id: str,
    payload: UnitUpdate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    if not _can_manage(user, db, unit_id):
        raise ForbiddenError("Acesso negado")
    return unit_service.update_unit(db, unit_id, payload)


@router.post("/{unit_id}/active", response_model=UnitOut)
def set_active(
    unit_id: str,
    is_active: bool,
    db: Session = Depends(get_db),
    _admin=Depends(require_roles("admin")),
):
    return unit_service.set_active(db, unit_id, is_active)


@router.get("/{unit_id}/capacity", response_model=list[CapacityOut])
def capacity(
    unit_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    if not _can_manage(user, db, unit_id):
        raise ForbiddenError("Acesso negado")
    return unit_service.list_capacity(db, unit_id)


@router.post("/{unit_id}/capacity", response_model=CapacityOut)
def update_capacity(
    unit_id: str,
    payload: CapacityIn,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    if not _can_manage(user, db, unit_id):
        raise ForbiddenError("Acesso negado")
    return unit_service.update_capacity(db, unit_id, payload, user.id)


@router.get("/{unit_id}/estimate")
def estimate(
    unit_id: str,
    recompute: bool = False,
    db: Session = Depends(get_db),
):
    return estimate_service.get_estimate(db, unit_id, recompute=recompute)
