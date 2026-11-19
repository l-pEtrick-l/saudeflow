from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import rate_limit, require_roles
from app.schemas.common import PageMeta
from app.schemas.integration import (
    ExternalUnitOut,
    IbgeMunicipioOut,
    PromoteExternalIn,
    RouteOut,
    SourceOut,
    SyncLogOut,
    SyncRequest,
    ViaCepOut,
)
from app.services import integration_service, unit_service

router = APIRouter(prefix="/integrations", tags=["Integrações externas"])


def _meta(total: int, page: int, page_size: int) -> dict:
    return PageMeta(
        page=page, page_size=page_size, total=total, total_pages=max(1, (total + page_size - 1) // page_size)
    ).model_dump()


@router.get("/sources", response_model=list[SourceOut])
def sources(db: Session = Depends(get_db), _admin=Depends(require_roles("admin"))):
    return integration_service.list_sources(db)


@router.post("/sync", response_model=SyncLogOut)
def sync(payload: SyncRequest, db: Session = Depends(get_db), _admin=Depends(require_roles("admin"))):
    return integration_service.sync_source(db, payload, triggered_by="admin")


@router.get("/sync-logs")
def sync_logs(
    source: str | None = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    _admin=Depends(require_roles("admin")),
):
    items, total = integration_service.list_sync_logs(db, page, page_size, source)
    return {"data": items, "meta": _meta(total, page, page_size)}


@router.get("/external-units")
def external_units(
    source: str | None = None,
    state: str | None = None,
    city: str | None = None,
    q: str | None = None,
    page: int = 1,
    page_size: int = 50,
    db: Session = Depends(get_db),
):
    items, total = integration_service.list_external(
        db, page, page_size, source, state, city, q
    )
    return {"data": items, "meta": _meta(total, page, page_size)}


@router.post("/external-units/{external_id}/promote")
def promote(
    external_id: str,
    payload: PromoteExternalIn,
    db: Session = Depends(get_db),
    _admin=Depends(require_roles("admin")),
):
    unit = integration_service.promote_external(db, external_id, payload)
    return unit_service.get_unit(db, unit.id)


@router.get("/viacep/{cep}", response_model=ViaCepOut)
def viacep(
    cep: str,
    db: Session = Depends(get_db),
    _limit=Depends(rate_limit(max_requests=30, window_seconds=60)),
):
    return integration_service.via_cep(db, cep)


@router.get("/ibge/municipios", response_model=list[IbgeMunicipioOut])
def ibge_municipios(
    uf: str = Query(..., min_length=2, max_length=2),
    db: Session = Depends(get_db),
    _limit=Depends(rate_limit(max_requests=60, window_seconds=60)),
):
    return integration_service.ibge_municipios(db, uf)


@router.get("/route", response_model=RouteOut)
def route(
    from_lat: float,
    from_lon: float,
    to_lat: float,
    to_lon: float,
    db: Session = Depends(get_db),
    _limit=Depends(rate_limit(max_requests=30, window_seconds=60)),
):
    return integration_service.osrm_route(db, from_lat, from_lon, to_lat, to_lon)
