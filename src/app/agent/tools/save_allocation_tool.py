import uuid

from langchain_core.tools import StructuredTool, tool
from pydantic import BaseModel, Field

from app.core.logging import get_logger
from app.repositories.allocation_repository import AllocationRepository

logger = get_logger(__name__)


class SaveAllocationInput(BaseModel):
    sneaker_id: int = Field(..., description="Id of the sneaker this allocation is for.")
    total_inventory: int = Field(..., description="Total units available across all regions.")
    demand_forecast: dict[str, float] = Field(
        ..., description="Mapping of region name to ML-predicted demand units."
    )
    forecast_analysis: str = Field(
        ...,
        description=(
            "Your analysis of the demand forecast itself, independent of the allocation "
            "decision: notable regional concentration or outliers, how much to trust the "
            "per-region numbers (see get_regional_demand_drivers), and anything else worth "
            "noting about the forecast before it's turned into an allocation."
        ),
    )
    allocation: dict[str, int] = Field(
        ..., description="Mapping of region name to units allocated to that region."
    )
    reasoning: str = Field(
        ..., description="Explanation of why this allocation was chosen."
    )


def make_save_allocation_tool(
    repository: AllocationRepository, conversation_id: uuid.UUID
) -> StructuredTool:
    @tool(
        description=(
            "Persist the final inventory allocation recommendation for this conversation, "
            "including the demand forecast and your analysis of it. Call this once, after "
            "you've reasoned over product info, warehouse capacity, and demand forecasts to "
            "arrive at a final allocation."
        ),
        args_schema=SaveAllocationInput,
    )
    async def save_allocation_recommendation(
        sneaker_id: int,
        total_inventory: int,
        demand_forecast: dict[str, float],
        forecast_analysis: str,
        allocation: dict[str, int],
        reasoning: str,
    ) -> dict[str, str]:
        logger.info("save_allocation_recommendation called: sneaker_id=%s", sneaker_id)
        record = await repository.save(
            conversation_id=conversation_id,
            sneaker_id=sneaker_id,
            total_inventory=total_inventory,
            demand_forecast=demand_forecast,
            forecast_analysis=forecast_analysis,
            allocation=allocation,
            reasoning=reasoning,
        )
        return {"allocation_id": str(record.id), "status": "saved"}

    return save_allocation_recommendation
