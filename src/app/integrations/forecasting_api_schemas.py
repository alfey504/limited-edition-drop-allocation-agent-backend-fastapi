from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class ForecastRequest(BaseModel):
    """Mirrors the forecasting API's ForecastRequest body (camelCase on the wire)."""

    model_config = ConfigDict(populate_by_name=True)

    buyer_regions: list[str] = Field(alias="buyerRegions")
    brand: str
    retail_price: float = Field(alias="retailPrice", gt=0)
    release_date: date = Field(alias="releaseDate")
    silhouette: str
    colorway_type: str = Field(alias="colorwayType")
