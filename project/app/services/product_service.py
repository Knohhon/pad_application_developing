from typing import Any, List, Optional
from uuid import UUID
from datetime import timedelta
from decimal import Decimal

from app.models.database_models import Product
from app.repositories.product_repository import ProductRepository
from app.schemas.product import ProductCreate, ProductUpdate
from sqlalchemy.ext.asyncio import AsyncSession
import json


class ProductService:
    def __init__(self, product_repository: ProductRepository, cache=None):
        self.product_repository = product_repository
        self.cache = cache
    
    def _serialize_product(self, product: Product) -> dict:
        """Преобразование объекта продукта в словарь для кэширования"""
        return {
            "id": str(product.id),
            "label": product.label,
            "count_in_package": product.count_in_package,
            "count_in_warehouse": product.count_in_warehouse,
            "price": str(product.price),
            "created_at": product.created_at.isoformat(),
            "updated_at": product.updated_at.isoformat()
        }
    
    async def get_by_id(self, session: AsyncSession, product_id: UUID) -> Optional[Product]:
        """Получить продукт по ID с использованием кэша при наличии"""
        if self.cache:
            # Пытаемся получить данные из кэша
            cached_data = self.cache.get_product(product_id)
            if cached_data:
                return Product(**cached_data)
        
        # Если нет в кэше или кэш не настроен, получаем из БД
        product = await self.product_repository.get_by_id(session, product_id)
        
        # Кэшируем результат, если кэш настроен
        if product and self.cache:
            self.cache.set_product(product_id, self._serialize_product(product))
        
        return product
    
    async def get_by_filter(
        self, session: AsyncSession, count: int = 10, page: int = 1, **kwargs: Any
    ) -> List[Product]:
        """Получить список продуктов с фильтрацией и пагинацией"""
        if count < 1 or count > 100:
            raise ValueError("Count must be between 1 and 100")
        if page < 1:
            raise ValueError("Page must be greater than 0")
        
        # Для списков обычно не используем кэш или используем с осторожностью
        return await self.product_repository.get_by_filter(
            session, count=count, page=page, **kwargs
        )
    
    async def create(self, session: AsyncSession, product_data: ProductCreate) -> Product:
        """Создать новый продукт с валидацией"""
        # Валидация данных
        if len(product_data.label) < 3:
            raise ValueError("Product label must be at least 3 characters long")
        if product_data.count_in_package < 1:
            raise ValueError("Count in package must be at least 1")
        if product_data.count_in_warehouse < 0:
            raise ValueError("Warehouse count cannot be negative")
        if product_data.price <= 0:
            raise ValueError("Price must be greater than zero")
        
        # Создаем продукт
        product = await self.product_repository.create(session, product_data)
        
        # Кэшируем новый продукт при наличии кэша
        if self.cache:
            self.cache.set_product(product.id, self._serialize_product(product))
        
        return product
    
    async def update(
        self, session: AsyncSession, product_id: UUID, product_data: ProductUpdate
    ) -> Product:
        """Обновить данные продукта и обновить кэш"""
        # Сначала получаем текущий продукт для валидации
        product = await self.get_by_id(session, product_id)
        if not product:
            raise ValueError(f"Product with id {product_id} not found")
        
        # Валидация обновленных данных
        if product_data.label and len(product_data.label) < 3:
            raise ValueError("Product label must be at least 3 characters long")
        
        if product_data.count_in_package is not None and product_data.count_in_package < 1:
            raise ValueError("Count in package must be at least 1")
        
        if product_data.count_in_warehouse is not None and product_data.count_in_warehouse < 0:
            raise ValueError("Warehouse count cannot be negative")
        
        if product_data.price is not None and product_data.price <= 0:
            raise ValueError("Price must be greater than zero")
        
        # Обновляем продукт в БД
        updated_product = await self.product_repository.update(session, product_id, product_data)
        
        # Обновляем кэш при наличии
        if self.cache:
            self.cache.update_product(product_id, self._serialize_product(updated_product))
        
        return updated_product
    
    async def delete(self, session: AsyncSession, product_id: UUID) -> None:
        """Удалить продукт и очистить кэш"""
        # Проверяем существование продукта
        product = await self.get_by_id(session, product_id)
        if not product:
            raise ValueError(f"Product with id {product_id} not found")
        
        # Удаляем продукт
        await self.product_repository.delete(session, product_id)
        
        # Удаляем из кэша при наличии
        if self.cache:
            self.cache.delete_product(product_id)
    
    async def update_stock(
        self, session: AsyncSession, product_id: UUID, quantity_change: int
    ) -> Product:
        """Обновить остатки продукта и обновить кэш"""
        # Используем метод из репозитория
        updated_product = await self.product_repository.update_stock(
            session, product_id, quantity_change
        )
        
        # Обновляем кэш при наличии
        if self.cache:
            self.cache.update_product(product_id, self._serialize_product(updated_product))
        
        return updated_product