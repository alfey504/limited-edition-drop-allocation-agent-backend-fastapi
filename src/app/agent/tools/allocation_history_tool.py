import uuid

from langchain_core.tools import StructuredTool, tool

from app.core.logging import get_logger
from app.db.models.allocation import AllocationRecommendation
from app.repositories.allocation_repository import AllocationRepository

logger = get_logger(__name__)


def _serialize_allocation(record: AllocationRecommendation) -> dict:
    return {
        "sneaker_id": record.sneaker_id,
        "total_inventory": record.total_inventory,
        "demand_forecast": record.demand_forecast,
        "forecast_analysis": record.forecast_analysis,
        "allocation": record.allocation,
        "reasoning": record.reasoning,
        "created_at": record.created_at.isoformat(),
    }


def make_allocation_history_tool(
    repository: AllocationRepository, conversation_id: uuid.UUID
) -> StructuredTool:
    @tool(
        description=(
            "Look up allocation recommendations already computed and saved earlier in this "
            "conversation, most recent first. Each entry has sneaker_id, total_inventory, "
            "demand_forecast, forecast_analysis, allocation, and reasoning exactly as they "
            "were saved. Always call this before generate_allocation_report_pdf to check "
            "whether an entry already exists for this sneaker — if one does, reuse its fields "
            "as-is in the report rather than recomputing or retyping them. Also use this "
            "instead of recalling numbers from memory when the user asks a follow-up question "
            "about a product already discussed. If nothing relevant comes back, re-call the "
            "original tools (get_product_launch_info, get_demand_forecast, etc.) instead of "
            "guessing."
        )
    )
    async def get_previous_allocations() -> list[dict]:
        logger.info("get_previous_allocations called: conversation_id=%s", conversation_id)
        records = await repository.list_for_conversation(conversation_id)
        return [_serialize_allocation(record) for record in records]

    return get_previous_allocations
