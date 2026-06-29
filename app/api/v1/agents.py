import json
from collections.abc import AsyncIterator
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from app.api.deps import get_agent_service, require_jwt
from app.schemas.agent import AgentInvokeRequest
from app.schemas.base import success_response
from app.services.agent_service import AgentService

router = APIRouter(dependencies=[Depends(require_jwt)])


@router.post("/invoke")
async def invoke_agent(
    request: Request,
    body: AgentInvokeRequest,
    agent_service: Annotated[AgentService, Depends(get_agent_service)],
) -> dict[str, Any]:
    request_id = getattr(request.state, "request_id", "unknown")
    result = await agent_service.invoke(body.thread_id, body.message)
    return success_response(result.model_dump(mode="json"), request_id).model_dump(mode="json")


async def _sse_generator(
    agent_service: AgentService,
    thread_id: str,
    message: str,
) -> AsyncIterator[str]:
    async for event_type, data in agent_service.stream(thread_id, message):
        yield f"event: {event_type}\ndata: {json.dumps(data)}\n\n"


@router.post("/stream")
async def stream_agent(
    body: AgentInvokeRequest,
    agent_service: Annotated[AgentService, Depends(get_agent_service)],
) -> StreamingResponse:
    return StreamingResponse(
        _sse_generator(agent_service, body.thread_id, body.message),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
