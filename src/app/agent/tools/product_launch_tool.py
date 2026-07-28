from langchain_core.tools import StructuredTool, tool
from pydantic import BaseModel, Field

from app.integrations.sneaker_api_client import SneakerApiClient
from app.integrations.sneaker_api_schemas import SneakerRead


class ProductLaunchInput(BaseModel):
    sneaker_id: int | None = Field(
        default=None,
        description="Exact catalog ID, if already known (e.g. from a prior lookup or an explicit SKU/ID in the user's message).",
    )
    query: str | None = Field(
        default=None,
        description="Free-text product description to search for, e.g. 'Jordan 4 Chicago' or 'the new handbag collection'.",
    )


def _serialize_sneaker(sneaker: SneakerRead) -> dict:
    return {
        "sneaker_id": sneaker.sneaker_id,
        "sneaker_name": sneaker.sneaker_name,
        "brand": sneaker.brand.brand,
        "silhouette": sneaker.silhouette.silhouette,
        "colorway": sneaker.colorway.colorway,
        "retail_price": float(sneaker.retail_price),
        "release_date": sneaker.release_date.isoformat(),
        "total_inventory": sneaker.inventory,
    }


def make_product_launch_tool(client: SneakerApiClient) -> StructuredTool:
    @tool(
        description=(
            "Get info about a product launch: product id, name, brand, silhouette, "
            "colorway, retail price, release date, and total inventory. "
            "Pass `sneaker_id` if you already have the exact id, `query` to search by "
            "free text (may return multiple candidates to disambiguate), or leave both "
            "empty to get the single soonest upcoming release."
        ),
        args_schema=ProductLaunchInput,
    )
    async def get_product_launch_info(
        sneaker_id: int | None = None, query: str | None = None
    ) -> dict | list[dict]:
        if sneaker_id is not None:
            sneaker = await client.get_sneaker(sneaker_id)
            if sneaker is None:
                return {"error": f"No sneaker found with id {sneaker_id}."}
            return _serialize_sneaker(sneaker)

        if query:
            candidates = await client.search_sneakers(query)
            if not candidates:
                return {"error": f"No sneakers matched '{query}'."}
            return [_serialize_sneaker(sneaker) for sneaker in candidates]

        next_release = await client.get_next_upcoming_sneaker()
        if next_release is None:
            return {"error": "No upcoming releases found."}
        return _serialize_sneaker(next_release)

    return get_product_launch_info
