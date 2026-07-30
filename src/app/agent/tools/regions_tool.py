from langchain_core.tools import StructuredTool, tool

from app.core.logging import get_logger
from app.integrations.sneaker_api_client import SneakerApiClient

logger = get_logger(__name__)


def make_regions_tool(client: SneakerApiClient) -> StructuredTool:
    @tool(
        description=(
            "Get the full list of regions that require an inventory allocation decision. Feed "
            "this list into get_demand_forecast's `buyer_regions` and cross-check it against "
            "get_warehouse_capacity — every region here should end up with an allocation "
            "decision, even if that decision is 0 units."
        )
    )
    async def get_regions() -> list[str]:
        logger.info("get_regions called")
        regions = await client.get_regions(limit=100)
        return [region.region for region in regions]

    return get_regions
