from pydantic import BaseModel, Field


class AgentInvokeRequest(BaseModel):
    thread_id: str = Field(..., min_length=1, description="Conversation thread ID for multi-turn")
    message: str = Field(..., min_length=1, description="User message to send to the agent")


class AgentInvokeResponse(BaseModel):
    thread_id: str
    message: str
    run_id: str | None = None


class AgentStreamTokenEvent(BaseModel):
    content: str


class AgentStreamDoneEvent(BaseModel):
    thread_id: str
    message: str
    run_id: str | None = None
