import asyncio
import threading
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1 import alerts as alerts_router
from app.api.v1 import analytics as analytics_router
from app.api.v1 import audit as audit_router
from app.api.v1 import auth as auth_router
from app.api.v1 import estimates as estimates_router
from app.api.v1 import health as health_router
from app.api.v1 import integrations as integrations_router
from app.api.v1 import notifications as notifications_router
from app.api.v1 import questionnaires as questionnaires_router
from app.api.v1 import queues as queues_router
from app.api.v1 import requests as requests_router
from app.api.v1 import units as units_router
from app.api.v1 import users as users_router
from app.api.v1 import ws as ws_router
from app.config import settings
from app.database import init_db
from app.exceptions import register_exception_handlers
from app.realtime import bus


def _sync_scheduler() -> None:
    import time

    from app.database import SessionLocal
    from app.schemas.integration import SyncRequest
    from app.services import integration_service

    interval = max(settings.SYNC_INTERVAL_MINUTES, 1) * 60
    while True:
        time.sleep(interval)
        db = SessionLocal()
        try:
            integration_service.sync_source(
                db, SyncRequest(source="cnes"), triggered_by="scheduler"
            )
        except Exception:  # noqa: BLE001
            pass
        finally:
            db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    loop = asyncio.get_running_loop()
    bus.bind(loop)
    consumer = asyncio.create_task(bus.consume())
    init_db()
    if settings.SYNC_ENABLED:
        threading.Thread(target=_sync_scheduler, daemon=True).start()
    yield
    consumer.cancel()


app = FastAPI(
    title="SaúdeFlow",
    description=(
        "Plataforma de orientação de acesso à saúde, filas virtuais e pré-alertas. "
        "Demonstração acadêmica com dados simulados — não substitui atendimento médico."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    openapi_url="/openapi.json",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
register_exception_handlers(app)

API_PREFIX = "/api/v1"
for module in (
    auth_router,
    users_router,
    units_router,
    questionnaires_router,
    requests_router,
    queues_router,
    alerts_router,
    estimates_router,
    notifications_router,
    analytics_router,
    integrations_router,
    audit_router,
    ws_router,
):
    app.include_router(module.router, prefix=API_PREFIX)

app.include_router(health_router.router)
app.include_router(health_router.router, prefix=API_PREFIX)

# ---- Modo standalone: serve o frontend construído (frontend/dist) ----
_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if _DIST.exists():
    _assets = _DIST / "assets"
    if _assets.exists():
        app.mount("/assets", StaticFiles(directory=str(_assets)), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(full_path: str):
        # não intercepta a API nem as rotas de documentação
        if full_path.startswith("api/") or full_path in {"docs", "redoc", "openapi.json"}:
            raise HTTPException(status_code=404, detail="Not Found")
        candidate = (_DIST / full_path).resolve()
        try:
            candidate.relative_to(_DIST.resolve())
        except ValueError:
            return FileResponse(_DIST / "index.html")
        if candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(_DIST / "index.html")
