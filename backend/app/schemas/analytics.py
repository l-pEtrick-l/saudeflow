from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel


class OverviewOut(BaseModel):
    total_units: int
    units_by_type: Dict[str, int]
    total_users: int
    total_requests: int
    requests_by_status: Dict[str, int]
    active_requests: int
    total_alerts: int
    alerts_by_status: Dict[str, int]
    average_attendance_minutes: Optional[float] = None
    last_24h_requests: int


class UnitStatsOut(BaseModel):
    unit_id: str
    unit_name: str
    requests_received: int
    pre_registers_confirmed: int
    patients_present: int
    awaiting_welcome: int
    in_care: int
    finished: int
    cancelled: int
    average_wait_minutes: Optional[float] = None
    capacity: dict
    estimate: dict
    alerts_received: int
    average_confirmation_minutes: Optional[float] = None
    by_day: List[dict]


class HospitalStatsOut(BaseModel):
    unit_id: str
    unit_name: str
    alerts_total: int
    alerts_by_status: Dict[str, int]
    patients_on_the_way: int
    average_confirmation_minutes: Optional[float] = None
    by_day: List[dict]
    by_city: List[dict]
