from langchain_core.tools import StructuredTool, tool
from pydantic import BaseModel, Field

from app.core.logging import get_logger

logger = get_logger(__name__)


class ForecastRatioInput(BaseModel):
    demand_forecast: dict[str, float] = Field(
        ...,
        description="Mapping of region name to ML-predicted demand units, from get_demand_forecast.",
    )


def make_forecast_ratio_tool() -> StructuredTool:
    @tool(
        description=(
            "Convert a demand forecast into each region's share of total demand (proportions "
            "summing to 1.0). Use this instead of estimating regional shares yourself before "
            "calling allocate_inventory."
        ),
        args_schema=ForecastRatioInput,
    )
    async def get_forecast_ratio(demand_forecast: dict[str, float]) -> dict[str, float]:
        logger.info("get_forecast_ratio called: regions=%s", list(demand_forecast))
        total_demand = sum(demand_forecast.values())
        if total_demand <= 0:
            region_count = len(demand_forecast)
            return {region: 1 / region_count for region in demand_forecast}
        return {region: demand / total_demand for region, demand in demand_forecast.items()}

    return get_forecast_ratio
