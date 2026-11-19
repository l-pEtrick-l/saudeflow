from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, get_current_user_optional, get_roles, get_unit_ids
from app.schemas.alert import AlertCreate, AlertOut, AlertUpdate
from app.schemas.common import PageMeta
from app.services import alert_service

router = APIRouter(prefix="/alerts", tags=["Pré-alertas de emergência"])


def _meta(total: int, page: int, page_size: int) -> dict:
    return PageMeta(
        page=page, page_size=page_size, total=total, total_pages=max(1, (total + page_size - 1) // page_size)
    ).model_dump()


@router.post("", response_model=AlertOut, status_code=201)
def create_alert(
    payload: AlertCreate,
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(get_current_user_optional),
):
    return alert_service.create_alert(
        db, payload, user.id if user else None, request.client.host if request.client else None
    )


@router.get("")
def list_alerts(
    status: str | None = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    is_admin = "admin" in get_roles(user, db)
    items, total = alert_service.list_alerts(
        db, user.id, is_admin, get_unit_ids(user, db), page, page_size, status
    )
    return {"data": items, "meta": _meta(total, page, page_size)}


@router.get("/{alert_id}", response_model=AlertOut)
def get_alert(
    alert_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return alert_service.get_alert(db, alert_id, user.id, "admin" in get_roles(user, db))


@router.patch("/{alert_id}", response_model=AlertOut)
def update_alert(
    alert_id: str,
    payload: AlertUpdate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return alert_service.update_status(
        db, alert_id, payload, user.id, "admin" in get_roles(user, db)
    )


@router.post("/{alert_id}/confirm", response_model=AlertOut)
def confirm(
    alert_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return alert_service.confirm(db, alert_id, user.id)
