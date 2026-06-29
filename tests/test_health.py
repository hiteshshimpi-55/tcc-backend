from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
import pytest
from langgraph.checkpoint.memory import MemorySaver

from app.agents.graph import build_graph
from app.config import Settings, get_settings
from app.logging import setup_logging
from app.main import create_app
from app.services.agent_service import AgentService
from tests.fakes import FakeChatModel


@pytest.mark.asyncio
async def test_liveness(client):
    response = await client.get("/api/v1/health/live")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["status"] == "alive"
    assert "request_id" in body["meta"]
    assert "X-Request-ID" in response.headers


@pytest.mark.asyncio
async def test_readiness_without_database(test_settings: Settings, fake_llm: FakeChatModel):
    get_settings.cache_clear()
    settings = test_settings.model_copy(
        update={"database_url": "postgresql://invalid:invalid@127.0.0.1:1/nodb"}
    )

    @asynccontextmanager
    async def lifespan(app) -> AsyncIterator[None]:
        app_settings: Settings = app.state.settings
        setup_logging(app_settings)
        checkpointer = MemorySaver()
        graph = build_graph(app_settings, checkpointer, llm=fake_llm)
        app.state.checkpointer = checkpointer
        app.state.agent_service = AgentService(graph)
        yield

    app = create_app(settings, lifespan_override=lifespan)

    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get("/api/v1/health/ready")

    assert response.status_code == 503
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "SERVICE_UNAVAILABLE"
