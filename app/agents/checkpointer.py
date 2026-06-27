from contextlib import AbstractAsyncContextManager
from typing import Any

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

CheckpointerContext = tuple[AsyncPostgresSaver, AbstractAsyncContextManager[Any]]


async def init_checkpointer(conn_string: str) -> CheckpointerContext:
    cm = AsyncPostgresSaver.from_conn_string(conn_string)
    checkpointer = await cm.__aenter__()
    await checkpointer.setup()
    return checkpointer, cm


async def close_checkpointer(context: CheckpointerContext) -> None:
    _, cm = context
    await cm.__aexit__(None, None, None)
