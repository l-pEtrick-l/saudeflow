from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.models.user import UserRole
from app.repositories.base import paged


def create(
    db: Session,
    title: str,
    body: Optional[str] = None,
    type: str = "info",
    user_id: Optional[str] = None,
    request_id: Optional[str] = None,
    alert_id: Optional[str] = None,
) -> Notification:
    notification = Notification(
        user_id=user_id,
        title=title,
        body=body,
        type=type,
        request_id=request_id,
        alert_id=alert_id,
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification


def list_for_user(db: Session, user_id: str, page: int, page_size: int, unread_only: bool = False):
    query = select(Notification).filter_by(user_id=user_id)
    if unread_only:
        query = query.filter(Notification.is_read.is_(False))
    query = query.order_by(Notification.created_at.desc())
    return paged(db, query, page, page_size)


def mark_read(db: Session, notification_id: str, user_id: str) -> None:
    notification = db.get(Notification, notification_id)
    if notification and notification.user_id == user_id:
        notification.is_read = True
        db.commit()


def mark_all_read(db: Session, user_id: str) -> None:
    db.query(Notification).filter_by(user_id=user_id, is_read=False).update(
        {Notification.is_read: True}
    )
    db.commit()


def notify_unit_staff(
    db: Session,
    unit_id: str,
    title: str,
    body: str,
    type: str = "info",
    request_id: Optional[str] = None,
    alert_id: Optional[str] = None,
) -> int:
    """Cria notificação para todos os usuários com vínculo ativo na unidade."""
    user_ids = db.scalars(
        select(UserRole.user_id).filter_by(unit_id=unit_id).distinct()
    ).all()
    count = 0
    for uid in user_ids:
        create(
            db,
            title=title,
            body=body,
            type=type,
            user_id=uid,
            request_id=request_id,
            alert_id=alert_id,
        )
        count += 1
    return count
