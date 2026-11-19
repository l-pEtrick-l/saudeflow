from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db

router = APIRouter(tags=["Saúde do sistema"])


@router.get("/health")
def health():
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "env": settings.ENV,
        "demo_mode": settings.DEMO_MODE,
    }


@router.get("/ready")
def ready(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ready", "database": "ok"}
    except Exception as exc:  # noqa: BLE001
        return {"status": "unavailable", "database": str(exc)}
