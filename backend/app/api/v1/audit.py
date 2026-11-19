from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_roles
from app.repositories import audit_repo
from app.schemas.audit import AuditLogOut
from app.schemas.common import PageMeta

router = APIRouter(prefix="/audit-logs", tags=["Auditoria"])


def _meta(total: int, page: int, page_size: int) -> dict:
    return PageMeta(
        page=page, page_size=page_size, total=total, total_pages=max(1, (total + page_size - 1) // page_size)
    ).model_dump()


@router.get("")
def list_logs(
    page: int = 1,
    page_size: int = 50,
    action: str | None = None,
    entity_type: str | None = None,
    db: Session = Depends(get_db),
    _admin=Depends(require_roles("admin")),
):
    items, total = audit_repo.list_logs(db, page, page_size, action, entity_type)
    return {"data": [AuditLogOut.model_validate(i) for i in items], "meta": _meta(total, page, page_size)}
