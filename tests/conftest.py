import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta

import httpx
import jwt
import pytest
from langgraph.checkpoint.memory import MemorySaver

from app.agents.graph import build_graph
from app.api.auth_jwt import SupabaseTokenClaims
from app.api.deps import require_jwt
from app.config import Settings, get_settings
from app.logging import setup_logging
from app.main import create_app
from app.services.agent_service import AgentService
from tests.fakes import FakeChatModel

TEST_SECRET = "test-jwt-secret-for-unit-tests"
TEST_SUPABASE_ID = uuid.UUID("11111111-1111-4111-8111-111111111111")


@pytest.fixture
def test_settings() -> Settings:
    get_settings.cache_clear()
    return Settings(
        app_env="development",
        debug=True,
        openai_api_key="test-key",
        database_url="postgresql://tcc:tcc@localhost:5432/tcc",
        api_key="",
        supabase_jwt_secret=TEST_SECRET,
    )


@pytest.fixture
def fake_llm() -> FakeChatModel:
    return FakeChatModel(responses=["Hello from the agent"])


def make_auth_header(supabase_id: uuid.UUID = TEST_SUPABASE_ID) -> dict[str, str]:
    token = jwt.encode(
        {
            "sub": str(supabase_id),
            "email": "test@example.com",
            "aud": "authenticated",
            "user_metadata": {"full_name": "Test User"},
            "exp": int((datetime.now(UTC) + timedelta(hours=1)).timestamp()),
        },
        TEST_SECRET,
        algorithm="HS256",
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def client(test_settings: Settings, fake_llm: FakeChatModel):
    get_settings.cache_clear()

    async def override_require_jwt() -> SupabaseTokenClaims:
        return SupabaseTokenClaims(
            supabase_id=TEST_SUPABASE_ID,
            email="test@example.com",
            full_name="Test User",
            avatar_url=None,
        )

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
    app.dependency_overrides[require_jwt] = override_require_jwt

    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test",
        ) as ac:
            yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers() -> dict[str, str]:
    return make_auth_header()
