"""Dependências FastAPI: autenticação, RBAC, paginação e rate limiting."""

import time
from collections import defaultdict, deque
from typing import Dict, List, Optional

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.exceptions import ForbiddenError, UnauthorizedError
from app.models.user import User, UserRole
from app.security import decode_token


def get_current_user_optional(
    request: Request, db: Session = Depends(get_db)
) -> Optional[User]:
    token = _extract_token(request)
    if not token:
        return None
    payload = decode_token(token)
    if not payload or payload.get("type") == "refresh":
        return None
    return db.get(User, payload.get("sub"))


def get_current_user(
    request: Request, db: Session = Depends(get_db)
) -> User:
    token = _extract_token(request)
    if not token:
        raise UnauthorizedError("Autenticação necessária", code="auth_required")
    payload = decode_token(token)
    if not payload:
        raise UnauthorizedError("Token inválido ou expirado", code="invalid_token")
    if payload.get("type") == "refresh":
        raise UnauthorizedError("Token de acesso inválido", code="wrong_token_type")
    user = db.get(User, payload.get("sub"))
    if not user or not user.is_active:
        raise UnauthorizedError("Usuário inativo ou inexistente", code="invalid_user")
    return user


def _extract_token(request: Request) -> Optional[str]:
    auth = request.headers.get("authorization")
    if auth and auth.lower().startswith("bearer "):
        return auth[7:].strip()
    return request.query_params.get("token")


def get_roles(user: User, db: Session) -> List[str]:
    return [ur.role.name for ur in db.query(UserRole).filter_by(user_id=user.id).all()]


def get_unit_ids(user: User, db: Session) -> List[str]:
    return [
        ur.unit_id
        for ur in db.query(UserRole)
        .filter_by(user_id=user.id)
        .filter(UserRole.unit_id.isnot(None))
        .all()
    ]


def require_roles(*roles: str):
    def _dep(
        user: User = Depends(get_current_user), db: Session = Depends(get_db)
    ) -> User:
        user_roles = set(get_roles(user, db))
        if not user_roles.intersection(roles):
            raise ForbiddenError(
                "Você não tem permissão para esta operação", code="forbidden_role"
            )
        return user

    return _dep


def require_unit_access(unit_id: str):
    """Garante que o usuário é admin ou tem vínculo com a unidade."""

    def _dep(
        user: User = Depends(get_current_user), db: Session = Depends(get_db)
    ) -> User:
        roles = set(get_roles(user, db))
        if "admin" in roles:
            return user
        if unit_id not in set(get_unit_ids(user, db)):
            raise ForbiddenError("Acesso negado a esta unidade", code="unit_forbidden")
        return user

    return _dep


class RateLimiter:
    """Limitador simples em memória (janela deslizante). Adequado ao MVP."""

    def __init__(self):
        self._hits: Dict[str, deque] = defaultdict(deque)

    def check(self, key: str, max_requests: int, window_seconds: int) -> bool:
        now = time.time()
        bucket = self._hits[key]
        while bucket and now - bucket[0] > window_seconds:
            bucket.popleft()
        if len(bucket) >= max_requests:
            return False
        bucket.append(now)
        return True


rate_limiter = RateLimiter()


def rate_limit(max_requests: int = 120, window_seconds: int = 60):
    def _dep(request: Request):
        key = request.client.host if request.client else "unknown"
        path = request.url.path
        if not rate_limiter.check(f"{key}:{path}", max_requests, window_seconds):
            raise ForbiddenError(
                "Limite de requisições excedido. Tente novamente em instantes.",
                code="rate_limited",
            )

    return _dep


class Pagination:
    def __init__(self, page: int = 1, page_size: int = 20):
        self.page = max(1, page)
        self.page_size = min(100, max(1, page_size))

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


def pagination(
    page: int = 1, page_size: int = 20
) -> Pagination:
    return Pagination(page=page, page_size=page_size)
