
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from decimal import Decimal


class ProductCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price: Decimal
    quantity: int


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[Decimal] = None
    quantity: Optional[int] = None


class ProductResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    price: Decimal
    quantity: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class InventoryReservation(BaseModel):
    product_id: int
    quantity: int


class InventoryReservationRequest(BaseModel):
    order_id: int
    items: list[InventoryReservation]
