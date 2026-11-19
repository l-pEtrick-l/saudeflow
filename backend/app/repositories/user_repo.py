from typing import List, Optional

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.exceptions import ConflictError
from app.models.user import Permission, Role, RolePermission, User, UserRole
from app.repositories.base import get_or_404, paged
from app.security import hash_password

DEFAULT_ROLES = {
    "admin": ["users:manage", "units:manage", "roles:manage", "audit:read", "integrations:manage"],
    "manager": ["units:edit", "capacity:edit", "queue:manage", "requests:manage", "analytics:read"],
    "receptionist": ["requests:manage", "queue:manage", "checkin:manage"],
    "classifier": ["requests:manage", "risk:classify", "queue:manage"],
    "operator": ["requests:read", "queue:read"],
    "hospital_staff": ["alerts:manage", "analytics:read"],
    "patient": ["requests:create", "alerts:create"],
}


def ensure_roles_and_permissions(db: Session) -> None:
    """Cria papéis e permissões padrão (idempotente)."""
    for perm_name in {p for perms in DEFAULT_ROLES.values() for p in perms}:
        if not db.scalar(select(Permission).filter_by(name=perm_name)):
            db.add(Permission(name=perm_name, description=perm_name))
    db.flush()
    for role_name, perm_names in DEFAULT_ROLES.items():
        role = db.scalar(select(Role).filter_by(name=role_name))
        if not role:
            role = Role(name=role_name, description=f"Papel {role_name}")
            db.add(role)
            db.flush()
        for perm_name in perm_names:
            perm = db.scalar(select(Permission).filter_by(name=perm_name))
            exists = db.scalar(
                select(RolePermission).filter_by(role_id=role.id, permission_id=perm.id)
            )
            if perm and not exists:
                db.add(RolePermission(role_id=role.id, permission_id=perm.id))
    db.commit()


def get_user(db: Session, user_id: str) -> Optional[User]:
    return db.get(User, user_id)


def get_by_email(db: Session, email: str) -> Optional[User]:
    return db.scalar(select(User).filter(func.lower(User.email) == email.lower()))


def create_user(db: Session, data: dict, role: str = "patient") -> User:
    if get_by_email(db, data["email"]):
        raise ConflictError("E-mail já cadastrado", code="email_exists")
    user = User(
        email=data["email"].lower(),
        hashed_password=hash_password(data["password"]),
        full_name=data["full_name"],
        phone=data.get("phone"),
        cpf=data.get("cpf"),
        birth_date=data.get("birth_date"),
    )
    db.add(user)
    db.flush()
    assign_role(db, user.id, role)
    db.commit()
    db.refresh(user)
    return user


def list_users(db: Session, page: int, page_size: int, search: Optional[str] = None):
    query = select(User).filter(User.deleted_at.is_(None))
    if search:
        like = f"%{search}%"
        query = query.filter(or_(User.full_name.ilike(like), User.email.ilike(like)))
    query = query.order_by(User.created_at.desc())
    return paged(db, query, page, page_size)


def update_user(db: Session, user: User, data: dict) -> User:
    for field, value in data.items():
        if value is not None:
            setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user


def soft_delete_user(db: Session, user: User) -> None:
    from datetime import datetime, timezone

    user.deleted_at = datetime.now(timezone.utc)
    user.is_active = False
    db.commit()


def get_role_by_name(db: Session, name: str) -> Optional[Role]:
    return db.scalar(select(Role).filter_by(name=name))


def list_roles(db: Session) -> List[Role]:
    return db.scalars(select(Role).order_by(Role.name)).all()


def list_permissions(db: Session) -> List[Permission]:
    return db.scalars(select(Permission).order_by(Permission.name)).all()


def assign_role(db: Session, user_id: str, role_name: str, unit_id: Optional[str] = None) -> UserRole:
    role = get_role_by_name(db, role_name)
    if not role:
        raise NotFoundError(f"Papel {role_name} inexistente", code="role_not_found")
    existing = db.scalar(
        select(UserRole).filter_by(user_id=user_id, role_id=role.id, unit_id=unit_id)
    )
    if existing:
        return existing
    user_role = UserRole(user_id=user_id, role_id=role.id, unit_id=unit_id)
    db.add(user_role)
    db.commit()
    db.refresh(user_role)
    return user_role


def remove_role(db: Session, user_id: str, role_name: str, unit_id: Optional[str] = None) -> None:
    role = get_role_by_name(db, role_name)
    if not role:
        return
    user_role = db.scalar(
        select(UserRole).filter_by(user_id=user_id, role_id=role.id, unit_id=unit_id)
    )
    if user_role:
        db.delete(user_role)
        db.commit()


def get_user_roles(db: Session, user_id: str) -> List[UserRole]:
    return db.scalars(select(UserRole).filter_by(user_id=user_id)).all()


def get_user_role_names(db: Session, user_id: str) -> List[str]:
    return [ur.role.name for ur in get_user_roles(db, user_id)]


def get_user_unit_ids(db: Session, user_id: str) -> List[str]:
    return [ur.unit_id for ur in get_user_roles(db, user_id) if ur.unit_id]
