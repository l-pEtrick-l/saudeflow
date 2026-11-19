from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, get_roles, get_unit_ids, require_roles
from app.exceptions import ForbiddenError, NotFoundError
from app.models.unit import HealthcareUnit
from app.repositories import unit_repo
from app.schemas.analytics import HospitalStatsOut, OverviewOut, UnitStatsOut
from app.services import analytics_service

router = APIRouter(prefix="/analytics", tags=["Indicadores"])


def _check_unit(user, db, unit_id: str):
    if "admin" in get_roles(user, db):
        return
    if unit_id not in get_unit_ids(user, db):
        raise ForbiddenError("Acesso negado a esta unidade")


@router.get("/overview", response_model=OverviewOut)
def overview(
    db: Session = Depends(get_db),
    _admin=Depends(require_roles("admin")),
):
    return analytics_service.overview(db)


@router.get("/units/{unit_id}", response_model=UnitStatsOut)
def unit_stats(
    unit_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    _check_unit(user, db, unit_id)
    return analytics_service.unit_stats(db, unit_id)


@router.get("/hospitals/{unit_id}", response_model=HospitalStatsOut)
def hospital_stats(
    unit_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    _check_unit(user, db, unit_id)
    return analytics_service.hospital_stats(db, unit_id)
