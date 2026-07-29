import uuid
from pathlib import Path

from langchain_core.tools import StructuredTool

from app.agent.tools.allocation_history_tool import make_allocation_history_tool
from app.agent.tools.allocation_report_tool import make_allocation_report_tool
from app.agent.tools.current_date_tool import make_current_date_tool
from app.agent.tools.date_range_tool import make_date_range_tool
from app.agent.tools.demand_forecast_tool import make_demand_forecast_tool
from app.agent.tools.product_launch_tool import make_product_launch_tool
from app.agent.tools.regional_demand_drivers_tool import make_regional_demand_drivers_tool
from app.agent.tools.regions_tool import make_regions_tool
from app.agent.tools.save_allocation_tool import make_save_allocation_tool
from app.agent.tools.sneakers_in_range_tool import make_sneakers_in_range_tool
from app.agent.tools.warehouse_capacity_tool import make_warehouse_capacity_tool
from app.integrations.forecasting_api_client import ForecastingApiClient
from app.integrations.sneaker_api_client import SneakerApiClient
from app.repositories.allocation_repository import AllocationRepository
from app.repositories.report_repository import ReportRepository


def build_tools(
    sneaker_client: SneakerApiClient,
    forecasting_client: ForecastingApiClient,
    allocation_repository: AllocationRepository,
    report_repository: ReportRepository,
    reports_dir: Path,
    user_id: uuid.UUID,
    conversation_id: uuid.UUID,
) -> list[StructuredTool]:
    return [
        make_product_launch_tool(sneaker_client),
        make_current_date_tool(),
        make_date_range_tool(),
        make_sneakers_in_range_tool(sneaker_client),
        make_regions_tool(sneaker_client),
        make_warehouse_capacity_tool(sneaker_client),
        make_demand_forecast_tool(forecasting_client),
        make_regional_demand_drivers_tool(),
        make_allocation_history_tool(allocation_repository, conversation_id),
        make_save_allocation_tool(allocation_repository, conversation_id),
        make_allocation_report_tool(reports_dir, report_repository, user_id, conversation_id),
    ]
