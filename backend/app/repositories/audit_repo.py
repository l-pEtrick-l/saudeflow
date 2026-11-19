from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audit import AuditLog
from app.repositories.base import paged


def log(
    db: Session,
    action: str,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    actor_user_id: Optional[str] = None,
    details: Optional[dict] = None,
    ip_address: Optional[str] = None,
) -> AuditLog:
    entry = AuditLog(
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        actor_user_id=actor_user_id,
        details=details,
        ip_address=ip_address,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def list_logs(
    db: Session,
    page: int = 1,
    page_size: int = 50,
    action: Optional[str] = None,
    entity_type: Optional[str] = None,
):
    query = select(AuditLog)
    if action:
        query = query.filter_by(action=action)
    if entity_type:
        query = query.filter_by(entity_type=entity_type)
    query = query.order_by(AuditLog.created_at.desc())
    return paged(db, query, page, page_size)
