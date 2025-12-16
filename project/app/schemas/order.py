from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, field_validator


class ProductInOrder(BaseModel):
    id: UUID
    label: str
    price: Decimal


class AddressInOrder(BaseModel):
    street: str
    city: str
    zip_code: str
    country: str


class OrderItemCreate(BaseModel):
    product_id: UUID
    quantity: int = 1

    @field_validator("quantity")
    @classmethod
    def validate_quantity(cls, v):
        if v < 1:
            raise ValueError("Quantity must be at least 1")
        return v


class OrderItemResponse(BaseModel):
    product: ProductInOrder
    quantity: int
    unit_price: Decimal


# Схемы для Order
class OrderCreate(BaseModel):
    user_id: UUID
    address_id: UUID
    items: List[OrderItemCreate]  # Список товаров в заказе

    @field_validator("items")
    @classmethod
    def validate_items(cls, v):
        if not v:
            raise ValueError("Order must contain at least one item")
        return v


class OrderResponse(BaseModel):
    id: UUID
    user_id: UUID
    address: AddressInOrder
    items: List[OrderItemResponse]
    total_amount: Decimal  # Рассчитывается автоматически
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OrderUpdate(BaseModel):
    address_id: Optional[UUID] = None
    # Обновление товаров в заказе обычно запрещено после создания
