from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import estimate_service

router = APIRouter(prefix="/estimates", tags=["Estimativas de espera"])


@router.get("/{unit_id}")
def estimate(unit_id: str, recompute: bool = False, db: Session = Depends(get_db)):
    return estimate_service.get_estimate(db, unit_id, recompute=recompute)
