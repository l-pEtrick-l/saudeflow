from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import (
    get_current_user,
    get_current_user_optional,
    get_roles,
    get_unit_ids,
    require_roles,
)
from app.exceptions import ForbiddenError
from app.models.user import User
from app.schemas.common import PageMeta
from app.schemas.request import (
    CancelIn,
    RequestCreate,
    RequestEventOut,
    RequestOut,
    RiskClassificationIn,
)
from app.schemas.common import StatusUpdateIn
from app.services import request_service

router = APIRouter(prefix="/requests", tags=["Solicitações de atendimento"])


def _meta(total: int, page: int, page_size: int) -> dict:
    return PageMeta(
        page=page, page_size=page_size, total=total, total_pages=max(1, (total + page_size - 1) // page_size)
    ).model_dump()


@router.post("", response_model=RequestOut, status_code=201)
def create_request(
    payload: RequestCreate,
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(get_current_user_optional),
):
    return request_service.create_request(
        db, payload, user.id if user else None, request.client.host if request.client else None
    )


@router.get("")
def list_requests(
    status: str | None = None,
    unit_id: str | None = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    is_admin = "admin" in get_roles(user, db)
    items, total = request_service.list_requests(
        db, user.id, is_admin, get_unit_ids(user, db), page, page_size, status, unit_id
    )
    return {"data": items, "meta": _meta(total, page, page_size)}


@router.get("/track/{protocol}")
def track(protocol: str, db: Session = Depends(get_db)):
    return request_service.track_request(db, protocol)


@router.get("/{request_id}", response_model=RequestOut)
def get_request(
    request_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    is_admin = "admin" in get_roles(user, db)
    return request_service.get_request(db, request_id, user.id, is_admin)


@router.patch("/{request_id}/status", response_model=RequestOut)
def update_status(
    request_id: str,
    payload: StatusUpdateIn,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    request = request_service.get_request(db, request_id, user.id, "admin" in get_roles(user, db))
    if "admin" not in get_roles(user, db) and request.unit_id not in get_unit_ids(user, db):
        raise ForbiddenError("Somente a equipe da unidade pode atualizar o atendimento")
    return request_service.update_status(
        db, request_id, payload.status, user.id, payload.note
    )


@router.post("/{request_id}/cancel", response_model=RequestOut)
def cancel(
    request_id: str,
    payload: CancelIn,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return request_service.cancel(
        db, request_id, payload, user.id, "admin" in get_roles(user, db)
    )


@router.get("/{request_id}/timeline", response_model=list[RequestEventOut])
def timeline(
    request_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return request_service.timeline(db, request_id, user.id, "admin" in get_roles(user, db))


@router.post("/{request_id}/risk-classification", response_model=RequestOut)
def risk_classification(
    request_id: str,
    payload: RiskClassificationIn,
    db: Session = Depends(get_db),
    user=Depends(require_roles("admin", "classifier", "manager")),
):
    return request_service.set_risk_classification(db, request_id, payload, user.id)
