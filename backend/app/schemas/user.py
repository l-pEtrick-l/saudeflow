from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.schemas.common import ORMModel


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str = Field(..., min_length=3, max_length=200)
    phone: Optional[str] = Field(None, max_length=30)
    cpf: Optional[str] = Field(None, max_length=14)
    birth_date: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: "UserOut"


class UserOut(ORMModel):
    id: str
    email: str
    full_name: str
    phone: Optional[str] = None
    cpf: Optional[str] = None
    birth_date: Optional[str] = None
    is_active: bool
    roles: List[str] = []
    unit_ids: List[str] = []
    created_at: datetime


class RoleOut(ORMModel):
    id: str
    name: str
    description: Optional[str] = None


class PermissionOut(ORMModel):
    id: str
    name: str
    description: Optional[str] = None


class AssignRoleIn(BaseModel):
    user_id: str
    role: str
    unit_id: Optional[str] = None


class UserUpdateIn(BaseModel):
    full_name: Optional[str] = Field(None, min_length=3, max_length=200)
    phone: Optional[str] = Field(None, max_length=30)
    is_active: Optional[bool] = None


UserOut.model_rebuild()
