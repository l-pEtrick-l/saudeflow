from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.schemas.user import TokenOut, UserCreate, UserLogin, UserOut
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["Autenticação"])


@router.post("/register", response_model=TokenOut, status_code=201)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    auth_service.register(db, payload)
    user = auth_service.authenticate(db, payload.email, payload.password)
    return auth_service.build_token(db, user)


@router.post("/login", response_model=TokenOut)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    user = auth_service.authenticate(db, payload.email, payload.password)
    return auth_service.build_token(db, user)


@router.post("/refresh", response_model=TokenOut)
def refresh(payload: dict, db: Session = Depends(get_db)):
    return auth_service.refresh(db, payload.get("refresh_token", ""))


@router.get("/me", response_model=UserOut)
def me(user=Depends(get_current_user), db: Session = Depends(get_db)):
    return auth_service.profile(db, user)
