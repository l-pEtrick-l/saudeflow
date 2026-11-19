"""Serviço de integrações: sincronização, cache e geolocalização."""

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.config import settings
from app.exceptions import ForbiddenError, NotFoundError, UnprocessableError
from app.integrations.adapters import (
    CNESAdapter,
    DatasusHospitaisLeitosAdapter,
    IbgeAdapter,
    IntegrationError,
    OsrmAdapter,
    ViaCepAdapter,
    classify_unit_type,
)
from app.repositories import integration_repo, unit_repo
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
from app.repositories import audit_repo


def _cache_ibge(db: Session, uf: str, municipios: List[dict]) -> None:
    integration_repo.set_setting(
        db, f"ibge:municipios:{uf.upper()}", json.dumps(municipios, ensure_ascii=False)
    )



def list_sources(db: Session) -> List[SourceOut]:
    integration_repo.ensure_sources(db)
    return [SourceOut.model_validate(s) for s in integration_repo.list_sources(db)]


def list_sync_logs(db: Session, page: int, page_size: int, source: Optional[str] = None):
    items, total = integration_repo.list_sync_logs(db, page, page_size, source)
    return [SyncLogOut.model_validate(l) for l in items], total


def list_external(
    db: Session,
    page: int = 1,
    page_size: int = 50,
    source: Optional[str] = None,
    state: Optional[str] = None,
    city: Optional[str] = None,
    q: Optional[str] = None,
):
    items, total = integration_repo.list_external(db, page, page_size, source, state, city, q)
    return [ExternalUnitOut.model_validate(e) for e in items], total


def sync_source(
    db: Session,
    payload: SyncRequest,
    triggered_by: str = "admin",
) -> SyncLogOut:
    """Sincroniza uma fonte externa para o cache local (sem chamada por usuário)."""
    integration_repo.ensure_sources(db)
    log = integration_repo.create_sync_log(db, payload.source, triggered_by)
    fetched = inserted = updated = 0
    try:
        if payload.source == "cnes":
            adapter = CNESAdapter()
            unit_types = adapter.fetch_unit_types()
            records = adapter.fetch(
                uf=payload.uf or settings.SYNC_DEFAULT_UF,
                limit=payload.limit,
            )
            for record in records:
                mapped = adapter.map_record(record, unit_types)
                _, created = integration_repo.upsert_external(db, mapped)
                fetched += 1
                inserted += 1 if created else 0
                updated += 0 if created else 1
        elif payload.source == "datasus_leitos":
            adapter = DatasusHospitaisLeitosAdapter()
            records = adapter.fetch(uf=payload.uf or settings.SYNC_DEFAULT_UF, limit=payload.limit)
            for record in records:
                mapped = adapter.map_record(record)
                _, created = integration_repo.upsert_external(db, mapped)
                fetched += 1
                inserted += 1 if created else 0
                updated += 0 if created else 1
        elif payload.source == "ibge":
            adapter = IbgeAdapter()
            municipios = adapter.fetch_municipios(payload.uf or settings.SYNC_DEFAULT_UF)
            _cache_ibge(db, payload.uf or settings.SYNC_DEFAULT_UF, municipios)
            fetched = len(municipios)
            inserted = len(municipios)
        elif payload.source in ("viacep", "osrm"):
            raise UnprocessableError(
                "Esta fonte é sob demanda e não possui sincronização em lote",
                code="on_demand_source",
            )
        else:
            raise UnprocessableError("Fonte desconhecida", code="unknown_source")

        integration_repo.update_sync_log(
            db,
            log.id,
            status="success",
            finished_at=datetime.now(timezone.utc),
            records_fetched=fetched,
            records_inserted=inserted,
            records_updated=updated,
        )
    except IntegrationError as exc:
        db.rollback()
        integration_repo.update_sync_log(
            db,
            log.id,
            status="failed",
            finished_at=datetime.now(timezone.utc),
            records_fetched=fetched,
            records_inserted=inserted,
            records_updated=updated,
            error=str(exc),
        )
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        integration_repo.update_sync_log(
            db,
            log.id,
            status="failed",
            finished_at=datetime.now(timezone.utc),
            records_fetched=fetched,
            records_inserted=inserted,
            records_updated=updated,
            error=str(exc),
        )
    audit_repo.log(
        db,
        action="integration.sync",
        entity_type="integration_source",
        entity_id=payload.source,
        details={"fetched": fetched, "inserted": inserted, "updated": updated},
    )
    log = integration_repo.list_sync_logs(db, page=1, page_size=1, source=payload.source)[0][0]
    return SyncLogOut.model_validate(log)


def promote_external(
    db: Session,
    external_unit_id: str,
    payload: PromoteExternalIn,
    actor_id: Optional[str] = None,
):
    external = integration_repo.get_external(db, external_unit_id)
    if not external:
        raise NotFoundError("Registro externo não encontrado")
    unit = unit_repo.create_unit(
        db,
        {
            "name": external.name,
            "type": payload.unit_type or classify_unit_type(external.type_name or ""),
            "cnes_code": external.cnes_code,
            "source": external.source,
            "is_simulated": payload.is_simulated,
            "street": external.street,
            "number": external.number,
            "neighborhood": external.neighborhood,
            "city": external.city,
            "state": external.state,
            "postal_code": external.postal_code,
            "latitude": external.latitude,
            "longitude": external.longitude,
            "phone": external.phone,
        },
        payload.services,
    )
    audit_repo.log(
        db,
        action="integration.promote",
        entity_type="external_unit",
        entity_id=external.id,
        actor_user_id=actor_id,
        details={"unit_id": unit.id},
    )
    return unit


def via_cep(db: Session, cep: str) -> ViaCepOut:
    digits = "".join(c for c in cep if c.isdigit())
    if len(digits) != 8:
        raise UnprocessableError("CEP inválido", code="invalid_cep")
    cache_key = f"viacep:{digits}"
    cached = integration_repo.get_setting(db, cache_key)
    if cached:
        return ViaCepOut(**json.loads(cached), source="viacep (cache)")
    adapter = ViaCepAdapter()
    data = adapter.fetch(digits)
    integration_repo.set_setting(db, cache_key, json.dumps(data, ensure_ascii=False))
    return ViaCepOut(**data)


def ibge_municipios(db: Session, uf: str) -> List[IbgeMunicipioOut]:
    cache_key = f"ibge:municipios:{uf.upper()}"
    cached = integration_repo.get_setting(db, cache_key)
    if cached:
        return [IbgeMunicipioOut(**item) for item in json.loads(cached)]
    adapter = IbgeAdapter()
    data = adapter.fetch_municipios(uf)
    integration_repo.set_setting(db, cache_key, json.dumps(data, ensure_ascii=False))
    return [IbgeMunicipioOut(**item) for item in data]


def osrm_route(
    db: Session, lat1: float, lon1: float, lat2: float, lon2: float
) -> RouteOut:
    key = "osrm:" + hashlib.sha1(
        f"{lat1:.5f},{lon1:.5f}->{lat2:.5f},{lon2:.5f}".encode()
    ).hexdigest()
    cached = integration_repo.get_setting(db, key)
    if cached:
        data = json.loads(cached)
        return RouteOut(**data, source="osrm (cache)", cached=True)
    adapter = OsrmAdapter()
    data = adapter.fetch(lat1, lon1, lat2, lon2)
    integration_repo.set_setting(db, key, json.dumps(data))
    return RouteOut(**data, cached=False)
