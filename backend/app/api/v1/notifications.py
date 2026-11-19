from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, get_roles, get_unit_ids
from app.exceptions import ForbiddenError
from app.schemas.common import PageMeta
from app.schemas.notification import NotificationMarkRead, NotificationOut
from app.services import notification_service

router = APIRouter(prefix="/notifications", tags=["Notificações"])


def _meta(total: int, page: int, page_size: int) -> dict:
    return PageMeta(
        page=page, page_size=page_size, total=total, total_pages=max(1, (total + page_size - 1) // page_size)
    ).model_dump()


@router.get("")
def list_notifications(
    page: int = 1,
    page_size: int = 20,
    unread_only: bool = False,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    items, total = notification_service.list_for_user(
        db, user.id, page, page_size, unread_only
    )
    return {"data": items, "meta": _meta(total, page, page_size)}


@router.patch("/{notification_id}/read", response_model=dict)
def mark_read(
    notification_id: str,
    payload: NotificationMarkRead,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    if payload.is_read:
        notification_service.mark_read(db, notification_id, user.id)
    return {"ok": True}


@router.post("/read-all", response_model=dict)
def read_all(db: Session = Depends(get_db), user=Depends(get_current_user)):
    notification_service.mark_all_read(db, user.id)
    return {"ok": True}
