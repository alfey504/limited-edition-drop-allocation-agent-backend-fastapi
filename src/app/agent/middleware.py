import json

from langchain.agents.middleware.types import AgentMiddleware, ToolCallRequest
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from app.agent.state import CapturedToolState

_CAPTURE_FIELD_BY_TOOL = {
    "get_product_launch_info": "product_launch_snapshot",
    "get_warehouse_capacity": "warehouse_capacity_snapshot",
    "get_demand_forecast": "demand_forecast_snapshot",
}

_ENFORCED_TOOLS = {"save_allocation_recommendation", "generate_allocation_report_pdf"}


class ToolOutputIntegrityMiddleware(AgentMiddleware):
    """
    Prevents the LLM's own arguments from being the only source of truth for
    numbers that already came from a tool earlier in the same conversation.

    - Captures get_product_launch_info / get_warehouse_capacity /
      get_demand_forecast results verbatim into state (CapturedToolState).
    - Before save_allocation_recommendation or generate_allocation_report_pdf
      actually run, overwrites their sneaker_id / total_inventory /
      sneaker_name / demand_forecast arguments with the captured snapshots,
      so a hallucinated or mistyped number can never reach the DB or PDF —
      regardless of what the LLM wrote in its own tool call.
    """

    state_schema = CapturedToolState

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

        forecast = state.get("demand_forecast_snapshot")
        if isinstance(forecast, dict) and "demand_forecast" in args:
            args["demand_forecast"] = forecast

        if args == original_args:
            return request
        return request.override(tool_call={**request.tool_call, "args": args})
