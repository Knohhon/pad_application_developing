from pydantic import BaseModel, field_validator
from uuid import UUID
from typing import Optional
from datetime import datetime
from decimal import Decimal

# Базовая схема для продуктов (общие поля)
class ProductBase(BaseModel):
    label: str
    count_in_package: int
    count_in_warehouse: int = 0
    price: Decimal  # Добавлено поле цены
    
    @field_validator('label')
    @classmethod
    def validate_label(cls, v: str) -> str:
        """Валидация названия продукта"""
        stripped = v.strip()
        if len(stripped) < 3:
            raise ValueError('Label must be at least 3 characters')
        if len(stripped) > 100:
            raise ValueError('Label cannot exceed 100 characters')
        return stripped

    @field_validator('count_in_package')
    @classmethod
    def validate_package_count(cls, v: int) -> int:
        """Валидация количества в упаковке"""
        if v < 1:
            raise ValueError('Count in package must be at least 1')
        if v > 10000:
            raise ValueError('Count in package cannot exceed 10,000')
        return v

    @field_validator('count_in_warehouse')
    @classmethod
    def validate_warehouse_count(cls, v: int) -> int:
        """Валидация остатков на складе"""
        if v < 0:
            raise ValueError('Warehouse count cannot be negative')
        return v
    
    @field_validator('price')
    @classmethod
    def validate_price(cls, v: Decimal) -> Decimal:
        """Валидация цены продукта"""
        if v <= 0:
            raise ValueError('Price must be greater than zero')
        if v > 1000000:  # 1 миллион - разумный максимум
            raise ValueError('Price cannot exceed 1,000,000')
        # Округление до 2 знаков после запятой
        return v.quantize(Decimal('0.01'))

# Схема для создания продукта
class ProductCreate(ProductBase):
    """Схема для создания нового продукта"""
    pass  # Наследует все валидации и поля от ProductBase

# Схема для обновления продукта
class ProductUpdate(BaseModel):
    """Схема для частичного обновления продукта"""
    label: Optional[str] = None
    count_in_package: Optional[int] = None
    count_in_warehouse: Optional[int] = None
    price: Optional[Decimal] = None

    @field_validator('label')
    @classmethod
    def validate_label(cls, v: Optional[str]) -> Optional[str]:
        """Валидация только если поле присутствует"""
        if v is None:
            return None
        stripped = v.strip()
        if len(stripped) < 3:
            raise ValueError('Label must be at least 3 characters')
        if len(stripped) > 100:
            raise ValueError('Label cannot exceed 100 characters')
        return stripped

    @field_validator('count_in_package')
    @classmethod
    def validate_package_count(cls, v: Optional[int]) -> Optional[int]:
        """Валидация только если поле присутствует"""
        if v is None:
            return None
        if v < 1:
            raise ValueError('Count in package must be at least 1')
        if v > 10000:
            raise ValueError('Count in package cannot exceed 10,000')
        return v

    @field_validator('count_in_warehouse')
    @classmethod
    def validate_warehouse_count(cls, v: Optional[int]) -> Optional[int]:
        """Валидация только если поле присутствует"""
        if v is None:
            return None
        if v < 0:
            raise ValueError('Warehouse count cannot be negative')
        return v
    
    @field_validator('price')
    @classmethod
    def validate_price(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        """Валидация только если поле присутствует"""
        if v is None:
            return None
        if v <= 0:
            raise ValueError('Price must be greater than zero')
        if v > 1000000:
            raise ValueError('Price cannot exceed 1,000,000')
        return v.quantize(Decimal('0.01'))

# Схема для ответа (полные данные продукта)
class ProductResponse(ProductBase):
    """Полная схема продукта для ответа API"""
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    # Вложенные объекты для связанных данных
    order_items: list = []  # Пустой список по умолчанию
    
    class Config:
        from_attributes = True  # Важно для Pydantic v2 (ранее orm_mode=True)