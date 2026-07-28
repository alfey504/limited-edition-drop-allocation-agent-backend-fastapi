import uuid
from pathlib import Path

from langchain.agents import create_agent
from langchain_core.language_models import BaseChatModel
from langgraph.graph.state import CompiledStateGraph

from app.agent.middleware import ToolOutputIntegrityMiddleware
from app.agent.prompts.system_prompt import SYSTEM_PROMPT
from app.agent.tools import build_tools
from app.integrations.forecasting_api_client import ForecastingApiClient
from app.integrations.sneaker_api_client import SneakerApiClient
from app.repositories.allocation_repository import AllocationRepository
from app.repositories.report_repository import ReportRepository


def build_agent_graph(
    llm: BaseChatModel,
    sneaker_client: SneakerApiClient,
    forecasting_client: ForecastingApiClient,
    allocation_repository: AllocationRepository,
    report_repository: ReportRepository,
    reports_dir: Path,
    user_id: uuid.UUID,
    conversation_id: uuid.UUID,
) -> CompiledStateGraph:
    """
    Builds one compiled agent per conversation turn. Deliberately built fresh
    each time rather than as a long-lived singleton, since its tools close over
    per-request dependencies (see agent/tools/__init__.py). No checkpointer:
    message history is loaded from and persisted to Neon via
    ConversationService/Message on every turn, so LangGraph's own thread-scoped
    persistence would just duplicate that at a coarser granularity.

    Uses langchain.agents.create_agent (langgraph.prebuilt.create_react_agent is
    deprecated in favor of this as of langchain 1.x). ToolOutputIntegrityMiddleware
    supplies the state schema and guards against the LLM mis-transcribing a
    number a tool already returned earlier in the conversation.
    """
    tools = build_tools(
        sneaker_client,
        forecasting_client,
        allocation_repository,
        report_repository,
        reports_dir,
        user_id,
        conversation_id,
    )
    return create_agent(
        model=llm,
        tools=tools,
        system_prompt=SYSTEM_PROMPT,
        middleware=[ToolOutputIntegrityMiddleware()],
    )
