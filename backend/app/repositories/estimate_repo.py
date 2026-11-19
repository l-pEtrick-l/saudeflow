from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.estimate import WaitEstimate


def get(db: Session, unit_id: str) -> Optional[WaitEstimate]:
    return db.scalar(select(WaitEstimate).filter_by(unit_id=unit_id))


def upsert(db: Session, unit_id: str, fields: dict) -> WaitEstimate:
    row = get(db, unit_id)
    if row is None:
        row = WaitEstimate(unit_id=unit_id, **fields)
        db.add(row)
    else:
        for key, value in fields.items():
            setattr(row, key, value)
    db.commit()
    db.refresh(row)
    return row
