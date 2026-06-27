from collections.abc import AsyncIterator
from typing import Any

import structlog
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph.state import CompiledStateGraph

from app.core.exceptions import AgentExecutionError
from app.schemas.agent import AgentInvokeResponse, AgentStreamDoneEvent, AgentStreamTokenEvent

logger = structlog.get_logger(__name__)


class AgentService:
    def __init__(self, graph: CompiledStateGraph) -> None:
        self._graph = graph

    def _config(self, thread_id: str) -> dict[str, Any]:
        return {"configurable": {"thread_id": thread_id}}

    @staticmethod
    def _extract_response(messages: list) -> str:
        for message in reversed(messages):
            if isinstance(message, AIMessage) and message.content:
                content = message.content
                if isinstance(content, str):
                    return content
                if isinstance(content, list):
                    text_parts = [
                        part.get("text", "")
                        for part in content
                        if isinstance(part, dict) and part.get("type") == "text"
                    ]
                    return "".join(text_parts)
        return ""

    async def invoke(self, thread_id: str, message: str) -> AgentInvokeResponse:
        try:
            result = await self._graph.ainvoke(
                {"messages": [HumanMessage(content=message)]},
                config=self._config(thread_id),
            )
            response_text = self._extract_response(result["messages"])
            return AgentInvokeResponse(
                thread_id=thread_id,
                message=response_text,
            )
        except Exception as exc:
            logger.exception("agent_invoke_failed", thread_id=thread_id, error=str(exc))
            raise AgentExecutionError(f"Agent execution failed: {exc}") from exc

    async def stream(
        self, thread_id: str, message: str
    ) -> AsyncIterator[tuple[str, dict[str, Any]]]:
        collected_tokens: list[str] = []
        try:
            async for event in self._graph.astream_events(
                {"messages": [HumanMessage(content=message)]},
                config=self._config(thread_id),
                version="v2",
            ):
                if event["event"] != "on_chat_model_stream":
                    continue
                chunk = event.get("data", {}).get("chunk")
                if chunk is None or not getattr(chunk, "content", None):
                    continue
                token = chunk.content
                if isinstance(token, str) and token:
                    collected_tokens.append(token)
                    yield "token", AgentStreamTokenEvent(content=token).model_dump(mode="json")

            full_message = "".join(collected_tokens)
            if not full_message:
                result = await self._graph.ainvoke(
                    {"messages": [HumanMessage(content=message)]},
                    config=self._config(thread_id),
                )
                full_message = self._extract_response(result["messages"])

            yield (
                "done",
                AgentStreamDoneEvent(
                    thread_id=thread_id,
                    message=full_message,
                ).model_dump(mode="json"),
            )
        except Exception as exc:
            logger.exception("agent_stream_failed", thread_id=thread_id, error=str(exc))
            raise AgentExecutionError(f"Agent stream failed: {exc}") from exc
