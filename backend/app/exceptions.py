"""Exceções de domínio e handlers globais."""

from typing import Any, Dict

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class AppException(Exception):
    status_code: int = 400
    code: str = "app_error"

    def __init__(self, message: str, code: str | None = None):
        self.message = message
        if code:
            self.code = code
        super().__init__(message)


class NotFoundError(AppException):
    status_code = 404
    code = "not_found"


class ConflictError(AppException):
    status_code = 409
    code = "conflict"


class UnauthorizedError(AppException):
    status_code = 401
    code = "unauthorized"


class ForbiddenError(AppException):
    status_code = 403
    code = "forbidden"


class UnprocessableError(AppException):
    status_code = 422
    code = "unprocessable"


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppException)
    async def _app_exc(request: Request, exc: AppException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.code, "message": exc.message}},
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_exc(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "validation_error",
                    "message": "Dados inválidos",
                    "details": _safe_errors(exc),
                }
            },
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http_exc(request: Request, exc: StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": "http_error",
                    "message": str(exc.detail) if exc.detail else "Erro",
                }
            },
        )

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "internal_error",
                    "message": "Erro interno. Tente novamente.",
                }
            },
        )


def _safe_errors(exc: RequestValidationError) -> Dict[str, Any]:
    """Remove valores enviados pelo cliente do detalhamento (não vazar dados)."""
    errors = []
    for err in exc.errors():
        errors.append(
            {
                "field": ".".join(str(p) for p in err.get("loc", []) if p != "body"),
                "type": err.get("type"),
                "message": err.get("msg"),
            }
        )
    return {"fields": errors}
