from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
import pytest
from langgraph.checkpoint.memory import MemorySaver

from app.agents.graph import build_graph
from app.logging import setup_logging
from app.main import create_app
from app.services.agent_service import AgentService
from tests.fakes import FakeChatModel


@pytest.mark.asyncio
async def test_agent_invoke_success(client):
    response = await client.post(
        "/api/v1/agents/invoke",
        json={"thread_id": "session-1", "message": "Hello"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["thread_id"] == "session-1"
    assert body["data"]["message"] == "Hello from the agent"
    assert "request_id" in body["meta"]


@pytest.mark.asyncio
async def test_agent_multi_turn_persistence(test_settings):
    multi_llm = FakeChatModel(
        responses=["First response", "Second response with context"],
    )

    @asynccontextmanager
    async def lifespan(app) -> AsyncIterator[None]:
        settings = app.state.settings
        setup_logging(settings)
        checkpointer = MemorySaver()
        graph = build_graph(settings, checkpointer, llm=multi_llm)
        app.state.agent_service = AgentService(graph)
        yield

    app = create_app(test_settings, lifespan_override=lifespan)

    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test",
        ) as ac:
            r1 = await ac.post(
                "/api/v1/agents/invoke",
                json={"thread_id": "persist-thread", "message": "First message"},
            )
            r2 = await ac.post(
                "/api/v1/agents/invoke",
                json={"thread_id": "persist-thread", "message": "Follow up"},
            )

    assert r1.json()["data"]["message"] == "First response"
    assert r2.json()["data"]["message"] == "Second response with context"
