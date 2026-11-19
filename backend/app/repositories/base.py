"""Repositórios — acesso a dados isolado dos serviços e roteadores."""

from typing import List, Tuple

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.exceptions import NotFoundError


def get_or_404(db: Session, model, entity_id: str, label: str = "Registro"):
    entity = db.get(model, entity_id)
    if entity is None:
        raise NotFoundError(f"{label} não encontrado", code="not_found")
    return entity


def paged(db: Session, query, page: int, page_size: int) -> Tuple[List, int]:
    total = db.execute(select(func.count()).select_from(query.subquery())).scalar() or 0
    items = db.execute(
        query.offset((page - 1) * page_size).limit(page_size)
    ).scalars().all()
    return list(items), int(total)
