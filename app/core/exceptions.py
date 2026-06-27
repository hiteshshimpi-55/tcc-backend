from typing import Any


class AppException(Exception):
    def __init__(
        self,
        message: str,
        *,
        code: str = "APP_ERROR",
        status_code: int = 500,
        details: list[dict[str, Any]] | None = None,
    ) -> None:
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details
        super().__init__(message)


class NotFoundError(AppException):
    def __init__(self, message: str = "Resource not found", **kwargs: Any) -> None:
        super().__init__(message, code="NOT_FOUND", status_code=404, **kwargs)


class ValidationError(AppException):
    def __init__(self, message: str = "Validation failed", **kwargs: Any) -> None:
        super().__init__(message, code="VALIDATION_ERROR", status_code=400, **kwargs)


class UnauthorizedError(AppException):
    def __init__(self, message: str = "Unauthorized", **kwargs: Any) -> None:
        super().__init__(message, code="UNAUTHORIZED", status_code=401, **kwargs)


class AgentExecutionError(AppException):
    def __init__(self, message: str = "Agent execution failed", **kwargs: Any) -> None:
        super().__init__(message, code="AGENT_EXECUTION_ERROR", status_code=500, **kwargs)
