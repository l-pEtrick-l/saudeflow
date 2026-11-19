from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class SourceOut(ORMModel):
    id: str
    code: str
    name: str
    base_url: Optional[str] = None
    enabled: bool
    rate_limit_rpm: int
    description: Optional[str] = None


class SyncRequest(BaseModel):
    source: str = Field(..., pattern="^(cnes|datasus_leitos|ibge|viacep|osrm)$")
    uf: Optional[str] = Field(None, max_length=2)
    municipio_ibge: Optional[int] = None
    limit: int = Field(200, ge=1, le=1000)


class SyncLogOut(ORMModel):
    id: str
    source: str
    status: str
    started_at: datetime
    finished_at: Optional[datetime] = None
    records_fetched: int
    records_inserted: int
    records_updated: int
    error: Optional[str] = None
    triggered_by: Optional[str] = None


class ExternalUnitOut(ORMModel):
    id: str
    source: str
    external_id: str
    name: Optional[str] = None
    type_code: Optional[str] = None
    type_name: Optional[str] = None
    street: Optional[str] = None
    number: Optional[str] = None
    neighborhood: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    phone: Optional[str] = None
    cnes_code: Optional[str] = None
    ibge_code: Optional[str] = None
    beds_total: Optional[int] = None
    beds_sus: Optional[int] = None
    fetched_at: datetime


class ViaCepOut(BaseModel):
    cep: str
    logradouro: Optional[str] = None
    complemento: Optional[str] = None
    bairro: Optional[str] = None
    localidade: Optional[str] = None
    uf: Optional[str] = None
    ibge: Optional[str] = None
    gia: Optional[str] = None
    ddd: Optional[str] = None
    siafi: Optional[str] = None
    source: str = "viacep"


class IbgeMunicipioOut(BaseModel):
    id: int
    nome: str
    microrregiao: Optional[str] = None
    mesorregiao: Optional[str] = None
    uf: Optional[str] = None
    regiao: Optional[str] = None


class RouteOut(BaseModel):
    distance_km: float
    duration_minutes: float
    source: str = "osrm"
    cached: bool = False


class PromoteExternalIn(BaseModel):
    unit_type: str = Field(..., pattern="^(ubs|upa|hospital|emergency)$")
    is_simulated: bool = True
    services: List[dict] = []
