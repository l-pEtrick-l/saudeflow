from typing import Optional

from sqlalchemy.orm import Session

from app.repositories import notification_repo
from app.schemas.notification import NotificationOut


def list_for_user(db: Session, user_id: str, page: int, page_size: int, unread_only: bool = False):
    items, total = notification_repo.list_for_user(db, user_id, page, page_size, unread_only)
    return [NotificationOut.model_validate(n) for n in items], total


def mark_read(db: Session, notification_id: str, user_id: str) -> None:
    notification_repo.mark_read(db, notification_id, user_id)


def mark_all_read(db: Session, user_id: str) -> None:
    notification_repo.mark_all_read(db, user_id)
