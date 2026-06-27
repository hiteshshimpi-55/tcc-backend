from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import ChatOpenAI
from langgraph.graph import START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from app.agents.state import AgentState
from app.agents.tools import get_tools
from app.config import Settings


def _create_llm(settings: Settings) -> BaseChatModel:
    return ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key or None,
    )


def build_graph(
    settings: Settings,
    checkpointer: object,
    llm: BaseChatModel | None = None,
) -> CompiledStateGraph:
    llm = llm or _create_llm(settings)
    tools = get_tools()
    llm_with_tools = llm.bind_tools(tools)

    async def agent_node(state: AgentState) -> dict:
        response = await llm_with_tools.ainvoke(state["messages"])
        return {"messages": [response]}

    tool_node = ToolNode(tools)

    graph = StateGraph(AgentState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node)
    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", tools_condition)
    graph.add_edge("tools", "agent")

    return graph.compile(checkpointer=checkpointer)
