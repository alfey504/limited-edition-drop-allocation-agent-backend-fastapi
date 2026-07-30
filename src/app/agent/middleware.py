import json
from typing import override

from langchain.agents.middleware.types import AgentMiddleware, ToolCallRequest
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from app.agent.state import CapturedToolState

_CAPTURE_FIELD_BY_TOOL = {
    "get_product_launch_info": "product_launch_snapshot",
    "get_warehouse_capacity": "warehouse_capacity_snapshot",
    "get_demand_forecast": "demand_forecast_snapshot",
    "get_forecast_ratio": "forecast_ratio_snapshot",
    "allocate_inventory": "allocation_snapshot",
    "get_previous_allocations": "previous_allocations_snapshot",
}

_ENFORCED_TOOLS = {
    "get_forecast_ratio",
    "allocate_inventory",
    "save_allocation_recommendation",
    "generate_allocation_report_pdf",
}


class ToolOutputIntegrityMiddleware(AgentMiddleware):
    """
    Prevents the LLM's own arguments from being the only source of truth for
    numbers that already came from a tool earlier in the same conversation.

    - Captures get_product_launch_info / get_warehouse_capacity /
      get_demand_forecast / get_forecast_ratio / allocate_inventory /
      get_previous_allocations results verbatim into state (CapturedToolState).
    - Before get_forecast_ratio, allocate_inventory, save_allocation_recommendation,
      or generate_allocation_report_pdf actually run, overwrites their
      sneaker_id / total_inventory / sneaker_name / demand_forecast / ratios /
      warehouse_capacity / allocation arguments with the captured snapshots,
      so a hallucinated or mistyped number (including the allocation math
      itself) can never reach the DB or PDF — regardless of what the LLM
      wrote in its own tool call.
    - If save_allocation_recommendation/generate_allocation_report_pdf are
      called without a fresh in-turn demand_forecast_snapshot/allocation_snapshot
      (e.g. the LLM is reusing an allocation from an earlier turn instead of
      recomputing it), falls back to the matching get_previous_allocations
      record for that sneaker_id instead of trusting the LLM's own retyped
      copy of it — otherwise a region silently dropped while retyping (as
      happened in production) would go uncaught.
    """

    state_schema = CapturedToolState
    
    @override
    async def awrap_tool_call(self, request: ToolCallRequest, handler):
        tool_name = request.tool_call["name"]

        if tool_name in _ENFORCED_TOOLS:
            request = self._enforce_captured_values(request)

        result = await handler(request)

        capture_field = _CAPTURE_FIELD_BY_TOOL.get(tool_name)
        if capture_field is not None and isinstance(result, ToolMessage):
            return Command(
                update={"messages": [result], capture_field: json.loads(result.content)}
            )
        return result

    def _enforce_captured_values(self, request: ToolCallRequest) -> ToolCallRequest:
        state: CapturedToolState = request.state
        args = dict(request.tool_call["args"])
        original_args = dict(args)

        product = state.get("product_launch_snapshot")
        if isinstance(product, dict) and "error" not in product:
            for key in ("sneaker_id", "total_inventory", "sneaker_name"):
                if key in args and key in product:
                    args[key] = product[key]

        previous = self._find_previous_allocation(state, args.get("sneaker_id"))

        forecast = state.get("demand_forecast_snapshot")
        if isinstance(forecast, dict) and "demand_forecast" in args:
            args["demand_forecast"] = forecast
        elif previous is not None and "demand_forecast" in args:
            args["demand_forecast"] = previous["demand_forecast"]

        capacity = state.get("warehouse_capacity_snapshot")
        if isinstance(capacity, dict) and "warehouse_capacity" in args:
            args["warehouse_capacity"] = capacity

        ratios = state.get("forecast_ratio_snapshot")
        if isinstance(ratios, dict) and "ratios" in args:
            args["ratios"] = ratios

        allocation = state.get("allocation_snapshot")
        if isinstance(allocation, dict) and "allocation" in args:
            args["allocation"] = allocation
        elif previous is not None and "allocation" in args:
            args["allocation"] = previous["allocation"]

        if previous is not None:
            if "forecast_analysis" in args:
                args["forecast_analysis"] = previous["forecast_analysis"]
            if "reasoning" in args:
                args["reasoning"] = previous["reasoning"]

        if args == original_args:
            return request
        return request.override(tool_call={**request.tool_call, "args": args})

    def _find_previous_allocation(self, state: CapturedToolState, sneaker_id) -> dict | None:
        """Most recent get_previous_allocations record for sneaker_id, if any was captured."""
        records = state.get("previous_allocations_snapshot")
        if not isinstance(records, list) or sneaker_id is None:
            return None
        for record in records:
            if isinstance(record, dict) and record.get("sneaker_id") == sneaker_id:
                return record
        return None
