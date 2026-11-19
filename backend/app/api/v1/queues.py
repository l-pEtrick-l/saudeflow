from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, get_roles, get_unit_ids
from app.exceptions import ForbiddenError
from app.schemas.queue import CallNextOut, CheckInIn, QueueBoardOut
from app.services import queue_service

router = APIRouter(tags=["Filas e atendimento"])


class CareStartIn(BaseModel):
    professional_id: str | None = None


class CareFinishIn(BaseModel):
    outcome: str | None = None
    risk_classification: str | None = None
    classification_protocol: str | None = None
    notes: str | None = None


def _check_unit(user, db, unit_id: str):
    if "admin" in get_roles(user, db):
        return
    if unit_id not in get_unit_ids(user, db):
        raise ForbiddenError("Acesso negado a esta unidade")


def _check_request(user, db, request_id: str):
    from app.repositories import request_repo, unit_repo

    request = request_repo.get_request(db, request_id)
    if not request:
        return
    if "admin" in get_roles(user, db):
        return
    if request.unit_id not in get_unit_ids(user, db):
        raise ForbiddenError("Acesso negado a esta solicitação")


@router.get("/units/{unit_id}/queue/board", response_model=QueueBoardOut)
def board(
    unit_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    _check_unit(user, db, unit_id)
    return queue_service.board(db, unit_id)


@router.post("/units/{unit_id}/queue/call-next", response_model=CallNextOut)
def call_next(
    unit_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    _check_unit(user, db, unit_id)
    return queue_service.call_next(db, unit_id, user.id)


@router.get("/units/{unit_id}/attendances")
def attendances(
    unit_id: str,
    limit: int = 50,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    _check_unit(user, db, unit_id)
    return queue_service.list_attendances(db, unit_id, limit)


@router.post("/requests/{request_id}/confirm-receipt")
def confirm_receipt(
    request_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    _check_request(user, db, request_id)
    return queue_service.confirm_receipt(db, request_id, user.id)


@router.post("/requests/{request_id}/checkin")
def checkin(
    request_id: str,
    payload: CheckInIn,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    from app.repositories import request_repo

    request = request_repo.get_request(db, request_id)
    if not request:
        return {"error": "not_found"}
    _check_request(user, db, request_id)
    return queue_service.checkin(db, request_id, request.unit_id, user.id, payload.method)


@router.post("/requests/{request_id}/care-start")
def care_start(
    request_id: str,
    payload: CareStartIn,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    _check_request(user, db, request_id)
    return queue_service.start_care(db, request_id, user.id, payload.professional_id)


@router.post("/requests/{request_id}/care-finish")
def care_finish(
    request_id: str,
    payload: CareFinishIn,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    _check_request(user, db, request_id)
    return queue_service.finish_care(
        db,
        request_id,
        user.id,
        outcome=payload.outcome,
        risk_classification=payload.risk_classification,
        classification_protocol=payload.classification_protocol,
        notes=payload.notes,
    )
