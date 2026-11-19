from typing import Optional

from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories import user_repo
from app.schemas.user import UserOut


def list_users(db: Session, page: int, page_size: int, search: Optional[str] = None):
    items, total = user_repo.list_users(db, page, page_size, search)
    return [UserOut(
        id=u.id,
        email=u.email,
        full_name=u.full_name,
        phone=u.phone,
        cpf=u.cpf,
        birth_date=u.birth_date.isoformat() if u.birth_date else None,
        is_active=u.is_active,
        roles=user_repo.get_user_role_names(db, u.id),
        unit_ids=user_repo.get_user_unit_ids(db, u.id),
        created_at=u.created_at,
    ) for u in items], total


def get_user(db: Session, user_id: str) -> User:
    user = user_repo.get_user(db, user_id)
    if not user:
        from app.exceptions import NotFoundError

        raise NotFoundError("Usuário não encontrado")
    return user


def update_user(db: Session, user: User, data: dict) -> User:
    return user_repo.update_user(db, user, data)


def deactivate(db: Session, user: User) -> None:
    user_repo.update_user(db, user, {"is_active": False})


def assign_role(db: Session, user_id: str, role: str, unit_id: Optional[str]) -> None:
    user_repo.assign_role(db, user_id, role, unit_id)


def remove_role(db: Session, user_id: str, role: str, unit_id: Optional[str]) -> None:
    user_repo.remove_role(db, user_id, role, unit_id)


def list_roles(db: Session):
    return user_repo.list_roles(db)


def user_out(db: Session, user: User) -> UserOut:
    return UserOut(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        phone=user.phone,
        cpf=user.cpf,
        birth_date=user.birth_date.isoformat() if user.birth_date else None,
        is_active=user.is_active,
        roles=user_repo.get_user_role_names(db, user.id),
        unit_ids=user_repo.get_user_unit_ids(db, user.id),
        created_at=user.created_at,
    )

