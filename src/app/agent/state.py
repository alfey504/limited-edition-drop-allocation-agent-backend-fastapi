from typing import TypedDict


class CapturedToolState(TypedDict, total=False):
    """
    Verbatim snapshots of selected tool results, written by
    ToolOutputIntegrityMiddleware. These exist so the numbers that end up
    persisted (via save_allocation_recommendation / generate_allocation_report_pdf)
    are the real tool output, not the LLM's transcription of it.
    """

    product_launch_snapshot: dict | list | None
    warehouse_capacity_snapshot: dict[str, int] | None
    demand_forecast_snapshot: dict[str, float] | None
