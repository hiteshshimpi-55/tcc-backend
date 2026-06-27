from datetime import UTC, datetime

import structlog
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import Settings
from app.core.exceptions import AppException
from app.schemas.base import Meta, error_response

logger = structlog.get_logger(__name__)


def _get_request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "unknown")


def _meta(request: Request) -> Meta:
    return Meta(request_id=_get_request_id(request), timestamp=datetime.now(UTC))


def register_exception_handlers(app: FastAPI, settings: Settings) -> None:
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        body = error_response(
            code=exc.code,
            message=exc.message,
            meta=_meta(request),
            details=exc.details,
        )
        return JSONResponse(status_code=exc.status_code, content=body.model_dump(mode="json"))

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        details = [
            {
                "field": ".".join(str(loc) for loc in err["loc"]),
                "message": err["msg"],
            }
            for err in exc.errors()
        ]
        body = error_response(
            code="VALIDATION_ERROR",
            message="Request validation failed",
            meta=_meta(request),
            details=details,
        )
        return JSONResponse(status_code=422, content=body.model_dump(mode="json"))

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        code_map = {
            401: "UNAUTHORIZED",
            403: "FORBIDDEN",
            404: "NOT_FOUND",
            405: "METHOD_NOT_ALLOWED",
        }
        code = code_map.get(exc.status_code, "HTTP_ERROR")
        message = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
        body = error_response(code=code, message=message, meta=_meta(request))
        return JSONResponse(status_code=exc.status_code, content=body.model_dump(mode="json"))

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("unhandled_exception", error=str(exc))
        message = (
            "An internal server error occurred"
            if settings.is_production
            else f"Internal server error: {exc}"
        )
        body = error_response(
            code="INTERNAL_SERVER_ERROR",
            message=message,
            meta=_meta(request),
        )
        return JSONResponse(status_code=500, content=body.model_dump(mode="json"))
