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


@pytest.fixture
def test_settings() -> Settings:
    get_settings.cache_clear()
    return Settings(
        app_env="development",
        debug=True,
        openai_api_key="test-key",
        database_url="postgresql://tcc:tcc@localhost:5432/tcc",
        api_key="",
    )


@pytest.fixture
def fake_llm() -> FakeChatModel:
    return FakeChatModel(responses=["Hello from the agent"])


@pytest.fixture
async def client(test_settings: Settings, fake_llm: FakeChatModel):
    get_settings.cache_clear()

    @asynccontextmanager
    async def lifespan(app) -> AsyncIterator[None]:
        settings: Settings = app.state.settings
        setup_logging(settings)
        checkpointer = MemorySaver()
        graph = build_graph(settings, checkpointer, llm=fake_llm)
        app.state.checkpointer = checkpointer
        app.state.agent_service = AgentService(graph)
        yield

    app = create_app(test_settings, lifespan_override=lifespan)

    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test",
        ) as ac:
            yield ac
