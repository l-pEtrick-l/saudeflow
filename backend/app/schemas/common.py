"""Schemas Pydantic compartilhados."""

from typing import Any, Generic, List, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class ErrorOut(BaseModel):
    code: str
    message: str
    details: Optional[Any] = None


class PageMeta(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int


class Paginated(BaseModel, Generic[T]):
    data: List[T]
    meta: PageMeta


class OkOut(BaseModel):
    ok: bool = True
    message: Optional[str] = None


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class StatusUpdateIn(BaseModel):
    status: str = Field(..., min_length=1, max_length=30)
    note: Optional[str] = Field(None, max_length=1000)
