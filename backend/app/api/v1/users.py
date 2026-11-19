from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, pagination, require_roles
from app.models.user import User
from app.schemas.user import AssignRoleIn, RoleOut, UserOut, UserUpdateIn
from app.services import user_service

router = APIRouter(prefix="/users", tags=["Usuários"])


@router.get("", response_model=list[UserOut])
def list_users(
    page: int = 1,
    page_size: int = 20,
    search: str | None = None,
    db: Session = Depends(get_db),
    _admin=Depends(require_roles("admin")),
):
    items, _ = user_service.list_users(db, page, page_size, search)
    return items


@router.get("/{user_id}", response_model=UserOut)
def get_user(
    user_id: str,
    db: Session = Depends(get_db),
    _admin=Depends(require_roles("admin")),
):
    user = user_service.get_user(db, user_id)
    return user_service.user_out(db, user)


@router.patch("/{user_id}", response_model=UserOut)
def update_user(
    user_id: str,
    payload: UserUpdateIn,
    db: Session = Depends(get_db),
    _admin=Depends(require_roles("admin")),
):
    user = user_service.get_user(db, user_id)
    user_service.update_user(db, user, payload.model_dump(exclude_none=True))
    return user_service.user_out(db, user)


@router.post("/{user_id}/roles", response_model=UserOut)
def assign_role(
    user_id: str,
    payload: AssignRoleIn,
    db: Session = Depends(get_db),
    _admin=Depends(require_roles("admin")),
):
    user_service.assign_role(db, user_id, payload.role, payload.unit_id)
    return user_service.user_out(db, user_service.get_user(db, user_id))


@router.delete("/{user_id}/roles/{role}", response_model=UserOut)
def remove_role(
    user_id: str,
    role: str,
    unit_id: str | None = None,
    db: Session = Depends(get_db),
    _admin=Depends(require_roles("admin")),
):
    user_service.remove_role(db, user_id, role, unit_id)
    return user_service.user_out(db, user_service.get_user(db, user_id))


@router.get("/roles/list", response_model=list[RoleOut])
def roles(db: Session = Depends(get_db), _admin=Depends(require_roles("admin"))):
    return user_service.list_roles(db)

