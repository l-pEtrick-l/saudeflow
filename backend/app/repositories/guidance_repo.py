from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.guidance import GuidanceResult, GuidanceRule
from app.repositories.base import get_or_404


def list_rules(db: Session, rule_set_version: Optional[str] = None) -> List[GuidanceRule]:
    query = select(GuidanceRule).filter(GuidanceRule.is_active.is_(True))
    if rule_set_version:
        query = query.filter_by(rule_set_version=rule_set_version)
    return db.scalars(query.order_by(GuidanceRule.priority, GuidanceRule.name)).all()


def list_rule_sets(db: Session) -> List[str]:
    rows = db.execute(
        select(GuidanceRule.rule_set_version).distinct().order_by(GuidanceRule.rule_set_version)
    ).all()
    return [r[0] for r in rows]


def create_result(db: Session, submission_id: str, result: Dict[str, Any]) -> GuidanceResult:
    """Persiste o resultado mantendo apenas colunas mapeadas (descarta labels de apresentação)."""
    valid = {column.name for column in GuidanceResult.__table__.columns}
    data = {key: value for key, value in result.items() if key in valid}
    existing = get_result(db, submission_id)
    if existing:
        for key, value in data.items():
            setattr(existing, key, value)
        db.commit()
        db.refresh(existing)
        return existing
    row = GuidanceResult(submission_id=submission_id, **data)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def get_result(db: Session, submission_id: str) -> Optional[GuidanceResult]:
    return db.scalar(select(GuidanceResult).filter_by(submission_id=submission_id))
