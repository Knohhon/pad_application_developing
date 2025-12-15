from typing import Optional, List, Any
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.database_models import Product, OrderItem
from app.schemas.product import ProductCreate, ProductUpdate
from decimal import Decimal
from datetime import datetime

class ProductRepository:
    async def get_by_id(self, session: AsyncSession, product_id: UUID) -> Optional[Product]:
        """Get product by UUID with related order items preloaded"""
        result = await session.execute(
            select(Product)
            .options(selectinload(Product.order_items))
            .where(Product.id == product_id)
        )
        return result.scalar_one_or_none()

    async def get_by_filter(
        self,
        session: AsyncSession,
        count: int = 10,
        page: int = 1,
        **kwargs: Any
    ) -> List[Product]:
        """Get filtered product list with pagination and order items preloading"""
        query = select(Product).options(selectinload(Product.order_items))
        
        # Добавляем фильтрацию по price как по Decimal
        for key, value in kwargs.items():
            if hasattr(Product, key):
                if value is not None:
                    # Специальная обработка для цены
                    if key == 'price' and isinstance(value, (float, int)):
                        value = Decimal(str(value)).quantize(Decimal('0.01'))
                    query = query.where(getattr(Product, key) == value)
        
        offset = (page - 1) * count if page > 0 else 0
        query = query.offset(offset).limit(count)
        
        result = await session.execute(query)
        return list(result.scalars().all())

    async def create(
        self,
        session: AsyncSession,
        product_data: ProductCreate
    ) -> Product:
        """Create new product with auto-generated UUID and price handling"""
        # Валидация цены перед созданием
        if product_data.price <= 0:
            raise ValueError("Product price must be greater than zero")
        
        product_dict = product_data.model_dump(exclude_unset=True, exclude={"id"})
        
        # Обработка цены: преобразование в Decimal и округление
        if 'price' in product_dict:
            product_dict['price'] = Decimal(str(product_dict['price'])).quantize(Decimal('0.01'))
        
        new_product = Product(**product_dict)
        
        session.add(new_product)
        await session.commit()
        await session.refresh(new_product, attribute_names=["order_items"])
        return new_product

    async def update(
        self,
        session: AsyncSession,
        product_id: UUID,
        product_data: ProductUpdate
    ) -> Product:
        """Update product with automatic timestamp handling and price validation"""
        product = await self.get_by_id(session, product_id)
        if not product:
            raise ValueError(f"Product with id {product_id} not found")
        
        update_data = product_data.model_dump(exclude_unset=True)
        
        # Явное обновление отметки времени
        update_data['updated_at'] = datetime.now()
        
        # Валидация и обработка цены
        if 'price' in update_data:
            new_price = update_data['price']
            if new_price is not None:
                if new_price <= 0:
                    raise ValueError("Product price must be greater than zero")
                # Преобразование и округление цены
                update_data['price'] = Decimal(str(new_price)).quantize(Decimal('0.01'))
        
        # Применение обновлений
        for field, value in update_data.items():
            if hasattr(product, field) and value is not None:
                setattr(product, field, value)
        
        session.add(product)
        await session.commit()
        await session.refresh(product)
        return product

    async def delete(
        self,
        session: AsyncSession,
        product_id: UUID
    ) -> None:
        """Delete product with cascade handling for order items"""
        product = await self.get_by_id(session, product_id)
        if not product:
            raise ValueError(f"Product with id {product_id} not found")
        
        # Дополнительная проверка: нельзя удалить продукт, который есть в неотмененных заказах
        active_orders = await session.execute(
            select(OrderItem)
            .join(OrderItem.order)
            .where(OrderItem.product_id == product_id)
        )
        
        if active_orders.first():
            raise ValueError(
                "Cannot delete product that is referenced in existing orders. "
                "Consider archiving instead."
            )
        
        await session.delete(product)
        await session.commit()

    async def update_stock(
        self,
        session: AsyncSession,
        product_id: UUID,
        quantity_change: int
    ) -> Product:
        """Update product stock with validation"""
        product = await self.get_by_id(session, product_id)
        if not product:
            raise ValueError(f"Product with id {product_id} not found")
        
        new_stock = product.count_in_warehouse + quantity_change
        
        if new_stock < 0:
            raise ValueError(
                f"Insufficient stock. Current stock: {product.count_in_warehouse}, "
                f"Requested change: {quantity_change}"
            )
        
        product.count_in_warehouse = new_stock
        session.add(product)
        await session.commit()
        await session.refresh(product)
        return product

    async def get_low_stock_products(
        self,
        session: AsyncSession,
        threshold: int = 10,
        limit: int = 20
    ) -> List[Product]:
        """Get products with stock below threshold"""
        result = await session.execute(
            select(Product)
            .where(Product.count_in_warehouse <= threshold)
            .order_by(Product.count_in_warehouse)
            .limit(limit)
        )
        return list(result.scalars().all())