from datetime import UTC, datetime
from typing import Any

import psycopg
from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse

from app.config import Settings
from app.schemas.base import Meta, error_response, success_response

router = APIRouter()


@router.get("/live")
async def liveness(request: Request) -> dict[str, Any]:
    request_id = getattr(request.state, "request_id", "unknown")
    return success_response({"status": "alive"}, request_id).model_dump(mode="json")


@router.get("/ready")
async def readiness(request: Request) -> JSONResponse:
    settings: Settings = request.app.state.settings
    request_id = getattr(request.state, "request_id", "unknown")
    try:
        async with await psycopg.AsyncConnection.connect(settings.database_url) as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT 1")
                await cur.fetchone()
        body = success_response({"status": "ready"}, request_id).model_dump(mode="json")
        return JSONResponse(status_code=status.HTTP_200_OK, content=body)
    except Exception:
        body = error_response(
            code="SERVICE_UNAVAILABLE",
            message="Database not reachable",
            meta=Meta(request_id=request_id, timestamp=datetime.now(UTC)),
        ).model_dump(mode="json")
        return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content=body)
