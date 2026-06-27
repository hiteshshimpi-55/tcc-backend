from datetime import UTC, datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class Meta(BaseModel):
    request_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: list[dict[str, Any]] | None = None


class ApiResponse(BaseModel, Generic[T]):
    success: bool
    data: T | None = None
    error: ErrorDetail | None = None
    meta: Meta


def success_response(data: Any, request_id: str) -> ApiResponse[Any]:
    return ApiResponse(
        success=True,
        data=data,
        meta=Meta(request_id=request_id),
    )


def error_response(
    code: str,
    message: str,
    meta: Meta,
    details: list[dict[str, Any]] | None = None,
) -> ApiResponse[None]:
    return ApiResponse(
        success=False,
        error=ErrorDetail(code=code, message=message, details=details),
        meta=meta,
    )
