import uuid

from langchain_core.tools import StructuredTool, tool

from app.db.models.allocation import AllocationRecommendation
from app.repositories.allocation_repository import AllocationRepository


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
            "Look up allocation recommendations you already computed and saved earlier in "
            "this conversation, most recent first. Each entry includes the demand forecast "
            "that was used at the time, your forecast analysis, the allocation itself, and "
            "your reasoning — this is the demand forecast too, not just the allocation. Use "
            "this instead of recalling numbers from memory when the user asks a follow-up "
            "question about a product already discussed. If nothing relevant comes back, "
            "re-call the original tools (get_product_launch_info, get_demand_forecast, etc.) "
            "instead of guessing."
        )
    )
    async def get_previous_allocations() -> list[dict]:
        records = await repository.list_for_conversation(conversation_id)
        return [_serialize_allocation(record) for record in records]

    return get_previous_allocations
