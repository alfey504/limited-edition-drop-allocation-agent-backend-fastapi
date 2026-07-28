from langchain_core.tools import StructuredTool, tool

from app.core.logging import get_logger
from app.integrations.sneaker_api_client import SneakerApiClient

logger = get_logger(__name__)


def make_regions_tool(client: SneakerApiClient) -> StructuredTool:
    @tool(description="Get the list of regions that require inventory allocation.")
    async def get_regions() -> list[str]:
        logger.info("get_regions called")
        regions = await client.get_regions(limit=200)
        return [region.region for region in regions]

    return get_regions
