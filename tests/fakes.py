from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from pydantic import Field, PrivateAttr


class FakeChatModel(BaseChatModel):
    """Test double that supports bind_tools for LangGraph agent tests."""

    responses: list[str] = Field(default_factory=lambda: ["Hello from the agent"])

    _cursor: int = PrivateAttr(default=0)

    @property
    def _llm_type(self) -> str:
        return "fake-chat-model"

    def bind_tools(self, tools, **kwargs):  # noqa: ANN001
        return self

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):  # noqa: ANN001
        return self._make_result()

    async def _agenerate(self, messages, stop=None, run_manager=None, **kwargs):  # noqa: ANN001
        return self._make_result()

    def _make_result(self) -> ChatResult:
        if self._cursor >= len(self.responses):
            text = self.responses[-1]
        else:
            text = self.responses[self._cursor]
            self._cursor += 1
        message = AIMessage(content=text)
        return ChatResult(generations=[ChatGeneration(message=message)])
