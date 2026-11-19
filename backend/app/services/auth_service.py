from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.exceptions import UnauthorizedError
from app.models.user import User
from app.repositories import user_repo
from app.schemas.user import TokenOut, UserCreate, UserOut
from app.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)


def register(db: Session, payload: UserCreate) -> User:
    return user_repo.create_user(
        db,
        payload.model_dump(exclude_none=True),
        role="patient",
    )


def authenticate(db: Session, email: str, password: str) -> User:
    user = user_repo.get_by_email(db, email)
    if not user or not user.is_active:
        raise UnauthorizedError("Credenciais inválidas", code="invalid_credentials")
    if not verify_password(password, user.hashed_password):
        raise UnauthorizedError("Credenciais inválidas", code="invalid_credentials")
    return user


def build_token(db: Session, user: User) -> TokenOut:
    from app.config import settings

    roles = user_repo.get_user_role_names(db, user.id)
    unit_ids = user_repo.get_user_unit_ids(db, user.id)
    access = create_access_token(user.id, roles=roles, unit_ids=unit_ids)
    refresh = create_refresh_token(user.id)
    return TokenOut(
        access_token=access,
        refresh_token=refresh,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=profile(db, user),
    )


def refresh(db: Session, refresh_token: str) -> TokenOut:
    payload = decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise UnauthorizedError("Refresh token inválido", code="invalid_refresh")
    user = user_repo.get_user(db, payload.get("sub"))
    if not user or not user.is_active:
        raise UnauthorizedError("Usuário inválido", code="invalid_user")
    return build_token(db, user)


def profile(db: Session, user: User) -> UserOut:
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
