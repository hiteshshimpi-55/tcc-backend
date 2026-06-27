from typing import Annotated

from fastapi import Depends, Header, Request

from app.config import Settings, get_settings
from app.core.exceptions import UnauthorizedError
from app.services.agent_service import AgentService


def get_app_settings() -> Settings:
    return get_settings()


def get_agent_service(request: Request) -> AgentService:
    return request.app.state.agent_service


async def verify_api_key(
    settings: Annotated[Settings, Depends(get_app_settings)],
    x_api_key: Annotated[str | None, Header()] = None,
) -> None:
    if settings.api_key and x_api_key != settings.api_key:
        raise UnauthorizedError("Invalid or missing API key")
