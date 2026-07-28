from datetime import date

from app.core.config import Settings
from app.integrations.base_client import BaseApiClient
from app.integrations.exceptions import IntegrationResponseError
from app.integrations.sneaker_api_schemas import (
    RegionRead,
    RegionWarehouseCapacityRead,
    SneakerRead,
)


class SneakerApiClient(BaseApiClient):
    """Client for the limited-edition-drop-allocation-sneakers-dummy-api."""

    def __init__(self, settings: Settings) -> None:
        super().__init__(
            base_url=f"{settings.sneaker_api_base_url}/api/v1",
            api_key=settings.sneaker_api_key,
        )

    async def get_upcoming_sneakers(self, skip: int = 0, limit: int = 100) -> list[SneakerRead]:
        response = await self._request(
            "GET", "/sneakers/upcoming", params={"skip": skip, "limit": limit}
        )
        return [SneakerRead.model_validate(item) for item in response.json()]

    async def get_next_upcoming_sneaker(self) -> SneakerRead | None:
        try:
            response = await self._request("GET", "/sneakers/next")
        except IntegrationResponseError as exc:
            if exc.status_code == 404:
                return None
            raise
        return SneakerRead.model_validate(response.json())

    async def search_sneakers(self, query: str, limit: int = 10) -> list[SneakerRead]:
        response = await self._request(
            "GET", "/sneakers/search", params={"q": query, "limit": limit}
        )
        return [SneakerRead.model_validate(item) for item in response.json()]

    async def get_sneakers_in_range(
        self,
        start_date: date,
        end_date: date | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[SneakerRead]:
        params: dict[str, str | int] = {
            "start_date": start_date.isoformat(),
            "skip": skip,
            "limit": limit,
        }
        if end_date is not None:
            params["end_date"] = end_date.isoformat()

        response = await self._request("GET", "/sneakers/range", params=params)
        return [SneakerRead.model_validate(item) for item in response.json()]

    async def get_sneaker(self, sneaker_id: int) -> SneakerRead | None:
        try:
            response = await self._request("GET", f"/sneakers/{sneaker_id}")
        except IntegrationResponseError as exc:
            if exc.status_code == 404:
                return None
            raise
        return SneakerRead.model_validate(response.json())

    async def get_regions(self, skip: int = 0, limit: int = 100) -> list[RegionRead]:
        response = await self._request("GET", "/regions", params={"skip": skip, "limit": limit})
        return [RegionRead.model_validate(item) for item in response.json()]

    async def get_warehouse_capacities(
        self, skip: int = 0, limit: int = 100
    ) -> list[RegionWarehouseCapacityRead]:
        response = await self._request(
            "GET", "/regions/warehouse-capacity", params={"skip": skip, "limit": limit}
        )
        return [RegionWarehouseCapacityRead.model_validate(item) for item in response.json()]
