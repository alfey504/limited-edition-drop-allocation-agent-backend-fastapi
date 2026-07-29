from datetime import date

from langchain_core.tools import StructuredTool, tool

from app.core.logging import get_logger

logger = get_logger(__name__)

_WEEKDAY_NAMES = (
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday",
)


def make_current_date_tool() -> StructuredTool:
    @tool(
        description=(
            "Get today's date (server-local) and day of the week. Call this before "
            "resolving any relative time period like 'next week' or 'next month'."
        )
    )
    async def get_current_date() -> dict[str, str]:
        logger.info("get_current_date called")
        today = date.today()
        return {"date": today.isoformat(), "day_of_week": _WEEKDAY_NAMES[today.weekday()]}

    return get_current_date
