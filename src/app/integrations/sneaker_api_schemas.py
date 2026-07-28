from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class BrandRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    brand_id: int
    brand: str


class SilhouetteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    silhouette_id: int
    silhouette: str


class ColorwayRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    colorway_id: int
    colorway: str


class SneakerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    sneaker_id: int
    sneaker_name: str
    retail_price: Decimal
    release_date: date
    brand: BrandRead
    silhouette: SilhouetteRead
    colorway: ColorwayRead
    inventory: int


class RegionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    region_id: int
    region: str


class RegionWarehouseCapacityRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    region_warehouse_capacity_id: int
    capacity: int
    region: RegionRead
