from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ProductBase(BaseModel):
    sku: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=2, max_length=150)
    description: str | None = None
    price: Decimal = Field(ge=0, decimal_places=2)
    stock: int = Field(ge=0)
    active: bool = True


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    sku: str | None = Field(default=None, min_length=1, max_length=50)
    name: str | None = Field(default=None, min_length=2, max_length=150)
    description: str | None = None
    price: Decimal | None = Field(default=None, ge=0, decimal_places=2)
    stock: int | None = Field(default=None, ge=0)
    active: bool | None = None


class ProductResponse(ProductBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
