from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.integration import (
    ExternalUnit,
    IntegrationSetting,
    IntegrationSource,
    SyncLog,
)
from app.repositories.base import paged
from app.utils import new_uuid


def list_sources(db: Session) -> List[IntegrationSource]:
    return db.scalars(select(IntegrationSource).order_by(IntegrationSource.name)).all()


def get_source(db: Session, code: str) -> Optional[IntegrationSource]:
    return db.scalar(select(IntegrationSource).filter_by(code=code))


def ensure_sources(db: Session) -> None:
    from app.config import settings

    defaults = [
        ("cnes", "CNES — Estabelecimentos de Saúde (MS/DATASUS)", settings.CNES_BASE_URL, 60),
        ("datasus_leitos", "DATASUS — Hospitais e Leitos (MS/DATASUS)", settings.DATASUS_BASE_URL, 60),
        ("ibge", "IBGE — Localidades", settings.IBGE_BASE_URL, 120),
        ("viacep", "ViaCEP — Endereços por CEP", settings.VIACEP_BASE_URL, 60),
        ("osrm", "OSRM — Rotas (OpenStreetMap)", settings.OSRM_BASE_URL, 120),
    ]
    for code, name, base_url, rpm in defaults:
        if not get_source(db, code):
            db.add(
                IntegrationSource(
                    code=code, name=name, base_url=base_url, rate_limit_rpm=rpm
                )
            )
    db.commit()


def list_external(
    db: Session,
    page: int = 1,
    page_size: int = 50,
    source: Optional[str] = None,
    state: Optional[str] = None,
    city: Optional[str] = None,
    q: Optional[str] = None,
):
    query = select(ExternalUnit)
    if source:
        query = query.filter_by(source=source)
    if state:
        query = query.filter_by(state=state.upper())
    if city:
        query = query.filter(ExternalUnit.city.ilike(city))
    if q:
        query = query.filter(ExternalUnit.name.ilike(f"%{q}%"))
    query = query.order_by(ExternalUnit.fetched_at.desc())
    return paged(db, query, page, page_size)


def get_external(db: Session, external_unit_id: str) -> Optional[ExternalUnit]:
    return db.get(ExternalUnit, external_unit_id)


def get_external_by_source_id(db: Session, source: str, external_id: str) -> Optional[ExternalUnit]:
    return db.scalar(
        select(ExternalUnit).filter_by(source=source, external_id=external_id)
    )


def upsert_external(db: Session, data: dict) -> tuple:
    """Retorna (registro, criado?). Atualiza quando o hash dos dados mudou."""
    import hashlib
    import json

    existing = get_external_by_source_id(db, data["source"], data["external_id"])
    raw = json.dumps(data.get("source_data") or {}, sort_keys=True, ensure_ascii=False)
    new_hash = hashlib.sha256(raw.encode()).hexdigest()
    if existing:
        changed = getattr(existing, "_raw_hash", None) != new_hash
        for key, value in data.items():
            if key != "source_data":
                setattr(existing, key, value)
        existing.source_data = data.get("source_data")
        existing.fetched_at = data.get("fetched_at") or datetime.now(timezone.utc)
        db.commit()
        db.refresh(existing)
        return existing, False
    row = ExternalUnit(**{k: v for k, v in data.items() if k != "raw_hash"})
    row._raw_hash = new_hash  # tipo: ignorado pelo ORM
    row.fetched_at = data.get("fetched_at") or datetime.now(timezone.utc)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row, True


def create_sync_log(db: Session, source: str, triggered_by: str = "system") -> SyncLog:
    log = SyncLog(
        source=source, status="running", started_at=datetime.now(timezone.utc), triggered_by=triggered_by
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def update_sync_log(db: Session, log_id: str, **fields) -> None:
    log = db.get(SyncLog, log_id)
    if not log:
        return
    for key, value in fields.items():
        setattr(log, key, value)
    db.commit()


def list_sync_logs(db: Session, page: int = 1, page_size: int = 20, source: Optional[str] = None):
    query = select(SyncLog)
    if source:
        query = query.filter_by(source=source)
    query = query.order_by(SyncLog.started_at.desc())
    return paged(db, query, page, page_size)


def get_setting(db: Session, key: str) -> Optional[str]:
    row = db.get(IntegrationSetting, key)
    return row.value if row else None


def set_setting(db: Session, key: str, value: str) -> None:
    row = db.get(IntegrationSetting, key)
    if row:
        row.value = value
    else:
        db.add(IntegrationSetting(key=key, value=value))
    db.commit()
