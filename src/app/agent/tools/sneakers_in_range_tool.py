from datetime import date, timedelta

from langchain_core.tools import StructuredTool, tool
from pydantic import BaseModel, Field

from app.agent.tools.product_launch_tool import serialize_sneaker
from app.core.logging import get_logger
from app.integrations.sneaker_api_client import SneakerApiClient

logger = get_logger(__name__)


class SneakersInRangeInput(BaseModel):
    start_date: date = Field(..., description="First release date to include (inclusive).")
    end_date: date = Field(..., description="Last release date to include (inclusive).")


def make_sneakers_in_range_tool(client: SneakerApiClient) -> StructuredTool:
    @tool(
        description=(
            "Find every sneaker releasing within a date window, e.g. to answer 'what's "
            "releasing next week/month'. start_date and end_date are both inclusive — get "
            "them from resolve_date_range rather than computing them yourself. Returns an "
            "empty list if nothing releases in that window."
        ),
        args_schema=SneakersInRangeInput,
    )
    async def get_sneakers_releasing_in_range(start_date: date, end_date: date) -> list[dict]:
        logger.info(
            "get_sneakers_releasing_in_range called: start_date=%s end_date=%s",
            start_date, end_date,
        )
        # The underlying API's bounds are exclusive; widen by a day on each side so the
        # inclusive start_date/end_date this tool advertises actually behave as inclusive.
        sneakers = await client.get_sneakers_in_range(
            start_date=start_date - timedelta(days=1),
            end_date=end_date + timedelta(days=1),
            limit=100,
        )
        return [serialize_sneaker(sneaker) for sneaker in sneakers]

    return get_sneakers_releasing_in_range
