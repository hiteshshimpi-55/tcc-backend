from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI

from app.agents.checkpointer import close_checkpointer, init_checkpointer
from app.agents.graph import build_graph
from app.config import Settings
from app.db.session import run_migrations
from app.logging import setup_logging
from app.services.agent_service import AgentService

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings: Settings = app.state.settings
    setup_logging(settings)

    logger.info(
        "application_starting",
        app_name=settings.app_name,
        app_env=settings.app_env,
        langsmith_enabled=settings.langsmith_enabled,
    )

    run_migrations()
    logger.info("database_migrations_applied")

    checkpointer_context = await init_checkpointer(settings.database_url)
    checkpointer, cm = checkpointer_context
    app.state.checkpointer = checkpointer
    app.state.checkpointer_context = checkpointer_context

    graph = build_graph(settings, checkpointer)
    app.state.agent_service = AgentService(graph)

    logger.info("application_ready")

    yield

    await close_checkpointer(checkpointer_context)
    logger.info("application_shutdown")
