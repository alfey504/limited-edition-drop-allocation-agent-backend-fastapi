from app.core.config import Settings
from app.integrations.base_client import BaseApiClient
from app.integrations.forecasting_api_schemas import ForecastRequest


class ForecastingApiClient(BaseApiClient):
    """Client for the limited-edition-demand-forecasting-service-fast-api."""

    def __init__(self, settings: Settings) -> None:
        super().__init__(
            base_url=f"{settings.forecasting_api_base_url}/api/v1",
            api_key=settings.forecasting_api_key,
            timeout=15.0,
        )

    async def get_demand_forecast(self, request: ForecastRequest) -> dict[str, float]:
        response = await self._request(
            "POST", "/forecast", json=request.model_dump(mode="json", by_alias=True)
        )
        return response.json()

    async def health_check(self) -> bool:
        response = await self._request("GET", "/health")
        return response.is_success
