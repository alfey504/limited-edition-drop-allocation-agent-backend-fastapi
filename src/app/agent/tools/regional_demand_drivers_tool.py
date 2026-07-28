from functools import lru_cache
from pathlib import Path

from langchain_core.tools import StructuredTool, tool

_KNOWLEDGE_PATH = (
    Path(__file__).resolve().parent.parent / "knowledge" / "regional-demand-drivers.md"
)


@lru_cache(maxsize=1)
def _read_knowledge_file() -> str:
    return _KNOWLEDGE_PATH.read_text(encoding="utf-8")


def make_regional_demand_drivers_tool() -> StructuredTool:
    @tool(
        description=(
            "Get analyst notes on how sneaker demand is distributed across regions and why "
            "(from EDA on the forecasting model's training data), plus guidance on how to "
            "apply them to an allocation. Call this alongside get_demand_forecast and "
            "get_warehouse_capacity — it explains *why* demand skews the way it does and how "
            "much to trust a per-region prediction, not just the raw numbers."
        )
    )
    async def get_regional_demand_drivers() -> str:
        return _read_knowledge_file()

    return get_regional_demand_drivers
