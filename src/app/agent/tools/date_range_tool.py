import calendar
from datetime import date, timedelta
from enum import Enum

from langchain_core.tools import StructuredTool, tool
from pydantic import BaseModel, Field

from app.core.logging import get_logger

logger = get_logger(__name__)


class DateRangePeriod(str, Enum):
    THIS_WEEK = "this_week"
    NEXT_WEEK = "next_week"
    THIS_MONTH = "this_month"
    NEXT_MONTH = "next_month"


class DateRangeInput(BaseModel):
    period: DateRangePeriod = Field(
        ...,
        description=(
            "Relative period to resolve into concrete dates: 'this_week'/'next_week' "
            "(ISO calendar week, Monday-Sunday) or 'this_month'/'next_month' (calendar month)."
        ),
    )


def _week_bounds(monday: date) -> tuple[date, date]:
    return monday, monday + timedelta(days=6)


def _month_bounds(year: int, month: int) -> tuple[date, date]:
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, 1), date(year, month, last_day)


def make_date_range_tool() -> StructuredTool:
    @tool(
        description=(
            "Resolve a relative time period (e.g. 'next week', 'next month') into a concrete "
            "start_date/end_date, both inclusive. Weeks are ISO calendar weeks (Monday-Sunday); "
            "months are calendar months. Call get_current_date first to establish 'today' before "
            "picking a period, then pass the returned dates to get_sneakers_releasing_in_range."
        ),
        args_schema=DateRangeInput,
    )
    async def resolve_date_range(period: DateRangePeriod) -> dict[str, str]:
        logger.info("resolve_date_range called: period=%s", period)
        today = date.today()
        this_monday = today - timedelta(days=today.weekday())

        if period == DateRangePeriod.THIS_WEEK:
            start, end = _week_bounds(this_monday)
        elif period == DateRangePeriod.NEXT_WEEK:
            start, end = _week_bounds(this_monday + timedelta(days=7))
        elif period == DateRangePeriod.THIS_MONTH:
            start, end = _month_bounds(today.year, today.month)
        else:
            year, month = (
                (today.year, today.month + 1) if today.month < 12 else (today.year + 1, 1)
            )
            start, end = _month_bounds(year, month)

        return {"start_date": start.isoformat(), "end_date": end.isoformat()}

    return resolve_date_range
