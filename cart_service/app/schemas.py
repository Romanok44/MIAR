from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import List, Optional


class CartItemBase(BaseModel):
    product_id: UUID
    quantity: int


class CartItemCreate(CartItemBase):
    pass


class CartItemResponse(BaseModel):
    id: UUID
    product_id: UUID
    name: str
    quantity: int
    price: float
    total_price: float
    added_at: datetime

    class Config:
        from_attributes = True


class CartResponse(BaseModel):
    user_id: UUID
    items: List[CartItemResponse]
    total_price: float

    class Config:
        from_attributes = True


class ClearCartResponse(BaseModel):
    message: str = "Корзина очищена"
    cleared_at: datetime