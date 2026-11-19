from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class UnitServiceIn(BaseModel):
    service_code: str = Field(..., min_length=1, max_length=50)
    service_name: str = Field(..., min_length=1, max_length=150)
    is_available: bool = True
    notes: Optional[str] = None


class UnitServiceOut(ORMModel):
    id: str
    unit_id: str
    service_code: str
    service_name: str
    is_available: bool
    notes: Optional[str] = None


class UnitCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    type: str = Field(..., pattern="^(ubs|upa|hospital|emergency)$")
    cnes_code: Optional[str] = Field(None, max_length=20)
    is_simulated: bool = True
    street: Optional[str] = Field(None, max_length=255)
    number: Optional[str] = Field(None, max_length=20)
    complement: Optional[str] = Field(None, max_length=120)
    neighborhood: Optional[str] = Field(None, max_length=120)
    city: Optional[str] = Field(None, max_length=120)
    state: Optional[str] = Field(None, max_length=2)
    postal_code: Optional[str] = Field(None, max_length=10)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    phone: Optional[str] = Field(None, max_length=30)
    email: Optional[str] = Field(None, max_length=200)
    services: List[UnitServiceIn] = []


class UnitUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    type: Optional[str] = Field(None, pattern="^(ubs|upa|hospital|emergency)$")
    is_active: Optional[bool] = None
    is_simulated: Optional[bool] = None
    street: Optional[str] = None
    number: Optional[str] = None
    complement: Optional[str] = None
    neighborhood: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    phone: Optional[str] = None
    email: Optional[str] = None


class UnitOut(ORMModel):
    id: str
    name: str
    type: str
    cnes_code: Optional[str] = None
    source: str
    is_simulated: bool
    is_active: bool
    street: Optional[str] = None
    number: Optional[str] = None
    complement: Optional[str] = None
    neighborhood: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    services: List[UnitServiceOut] = []
    distance_km: Optional[float] = None
    estimate: Optional["UnitEstimate"] = None
    digital_queue_count: Optional[int] = None
    updated_at: Optional[datetime] = None


class UnitEstimate(BaseModel):
    is_reliable: bool
    low_minutes: Optional[float] = None
    p50_minutes: Optional[float] = None
    high_minutes: Optional[float] = None
    message: Optional[str] = None
    updated_at: Optional[datetime] = None


class CapacityIn(BaseModel):
    professionals_available: int = Field(..., ge=0, le=200)
    rooms_active: int = Field(..., ge=0, le=100)
    welcome_capacity: int = Field(..., ge=0, le=1000)
    services_unavailable: List[str] = []
    receiving_pre_registrations: bool = True
    exceptional_status: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = None


class CapacityOut(ORMModel):
    id: str
    unit_id: str
    professionals_available: int
    rooms_active: int
    welcome_capacity: int
    services_unavailable: List[str]
    receiving_pre_registrations: bool
    exceptional_status: Optional[str] = None
    notes: Optional[str] = None
    created_by: Optional[str] = None
    created_at: datetime


UnitOut.model_rebuild()
