from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class EstimateOut(BaseModel):
    unit_id: str
    is_reliable: bool
    low_minutes: Optional[float] = None
    p50_minutes: Optional[float] = None
    high_minutes: Optional[float] = None
    sample_size: int = 0
    method: Optional[str] = None
    message: str
    computed_at: Optional[datetime] = None


class UnitCardEstimate(BaseModel):
    is_reliable: bool
    low_minutes: Optional[float] = None
    p50_minutes: Optional[float] = None
    high_minutes: Optional[float] = None
    message: str
    updated_at: Optional[datetime] = None
