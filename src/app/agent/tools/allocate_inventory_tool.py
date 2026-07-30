from langchain_core.tools import StructuredTool, tool
from pydantic import BaseModel, Field

from app.core.logging import get_logger

logger = get_logger(__name__)


class AllocateInventoryInput(BaseModel):
    total_inventory: int = Field(..., description="Total units available across all regions.")
    ratios: dict[str, float] = Field(
        ..., description="Each region's share of total demand, from get_forecast_ratio."
    )
    warehouse_capacity: dict[str, int] = Field(
        ..., description="Each region's maximum storage, from get_warehouse_capacity."
    )


def _largest_remainder(total: int, ratios: dict[str, float]) -> dict[str, int]:
    """Splits `total` across regions by `ratios` so the result always sums to exactly `total`."""
    ideal = {region: ratio * total for region, ratio in ratios.items()}
    allocation = {region: int(value) for region, value in ideal.items()}
    leftover = total - sum(allocation.values())

    by_remainder = sorted(
        ideal, key=lambda region: ideal[region] - allocation[region], reverse=True
    )
    for region in by_remainder[:leftover]:
        allocation[region] += 1
    return allocation


def make_allocate_inventory_tool() -> StructuredTool:
    @tool(
        description=(
            "Turn total inventory into a final per-region allocation: splits total_inventory "
            "across regions in proportion to `ratios`, then caps each region at its warehouse "
            "capacity. Capped-off units are not redistributed to other regions — they're left "
            "unallocated as safety stock. Use this instead of computing the split yourself."
        ),
        args_schema=AllocateInventoryInput,
    )
    async def allocate_inventory(
        total_inventory: int,
        ratios: dict[str, float],
        warehouse_capacity: dict[str, int],
    ) -> dict[str, int]:
        logger.info(
            "allocate_inventory called: total_inventory=%s regions=%s",
            total_inventory, list(ratios),
        )
        raw_allocation = _largest_remainder(total_inventory, ratios)
        return {
            region: min(units, warehouse_capacity[region])
            for region, units in raw_allocation.items()
        }

    return allocate_inventory
