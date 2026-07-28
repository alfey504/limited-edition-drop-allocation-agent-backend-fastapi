from datetime import date

from langchain_core.tools import StructuredTool, tool
from pydantic import BaseModel, Field

from app.integrations.forecasting_api_client import ForecastingApiClient
from app.integrations.forecasting_api_schemas import ForecastRequest


class DemandForecastInput(BaseModel):
    buyer_regions: list[str] = Field(..., description="Regions to forecast demand for.")
    brand: str = Field(..., description="Sneaker brand, as returned by get_product_launch_info.")
    retail_price: float = Field(..., gt=0, description="Retail price in dollars.")
    release_date: date = Field(..., description="Release date (ISO 8601).")
    silhouette: str = Field(..., description="Silhouette, as returned by get_product_launch_info.")
    colorway_type: str = Field(
        ...,
        description=(
            "Colorway classification for the forecasting model (a constrained category, "
            "not the free-text colorway name from the catalog)."
        ),
    )


def make_demand_forecast_tool(client: ForecastingApiClient) -> StructuredTool:
    @tool(
        description=(
            "Get the ML-predicted demand (units) per region for a sneaker release. "
            "This is the only source of demand numbers — never estimate demand yourself."
        ),
        args_schema=DemandForecastInput,
    )
    async def get_demand_forecast(
        buyer_regions: list[str],
        brand: str,
        retail_price: float,
        release_date: date,
        silhouette: str,
        colorway_type: str,
    ) -> dict[str, float]:
        request = ForecastRequest(
            buyer_regions=buyer_regions,
            brand=brand,
            retail_price=retail_price,
            release_date=release_date,
            silhouette=silhouette,
            colorway_type=colorway_type,
        )
        return await client.get_demand_forecast(request)

    return get_demand_forecast
