from langchain_core.tools import StructuredTool, tool

from app.integrations.sneaker_api_client import SneakerApiClient


def make_warehouse_capacity_tool(client: SneakerApiClient) -> StructuredTool:
    @tool(
        description=(
            "Get warehouse storage capacity (max units) for every region, as a mapping "
            "of region name to capacity. Use this to cap how much inventory can actually "
            "be allocated to each region."
        )
    )
    async def get_warehouse_capacity() -> dict[str, int]:
        capacities = await client.get_warehouse_capacities(limit=200)
        return {capacity.region.region: capacity.capacity for capacity in capacities}

    return get_warehouse_capacity
