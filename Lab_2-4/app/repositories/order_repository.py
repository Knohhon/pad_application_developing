from typing import Optional, List
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.database_models import Order, OrderItem, Product
from app.schemas.order import OrderCreate
from decimal import Decimal

class OrderRepository:
    async def create(
        self,
        session: AsyncSession,
        order_data: OrderCreate
    ) -> Order:
        """Создать заказ с несколькими товарами"""
        # 1. Проверка существования пользователя и адреса
        # (реализация опущена для краткости)
        
        # 2. Создание заказа
        new_order = Order(
            user_id=order_data.user_id,
            address_id=order_data.address_id
        )
        session.add(new_order)
        await session.flush()  # Получаем ID без коммита
        
        # 3. Обработка позиций заказа
        total_amount = Decimal('0.00')
        for item in order_data.items:
            # 3.1 Получение продукта
            product = await session.get(Product, item.product_id)
            if not product:
                raise ValueError(f"Product {item.product_id} not found")
            
            # 3.2 Проверка остатков
            if product.count_in_warehouse < item.quantity:
                raise ValueError(
                    f"Not enough stock for {product.label}. "
                    f"Available: {product.count_in_warehouse}, "
                    f"Requested: {item.quantity}"
                )
            
            # 3.3 Создание позиции заказа
            order_item = OrderItem(
                order_id=new_order.id,
                product_id=item.product_id,
                quantity=item.quantity,
                unit_price=product.price
            )
            session.add(order_item)
            
            # 3.4 Расчет общей суммы
            total_amount += product.price * item.quantity
            
            # 3.5 Обновление остатков
            product.count_in_warehouse -= item.quantity
        
        # 4. Установка общей суммы (если нужно хранить в БД)
        # new_order.total_amount = total_amount
        
        await session.commit()
        await session.refresh(new_order, attribute_names=['items', 'address'])
        return new_order

    async def get_by_id(self, session: AsyncSession, order_id: UUID) -> Optional[Order]:
        """Получить заказ со всеми связями"""
        result = await session.execute(
            select(Order)
            .options(
                selectinload(Order.items).selectinload(OrderItem.product),
                selectinload(Order.address),
                selectinload(Order.user)
            )
            .where(Order.id == order_id)
        )
        return result.scalar_one_or_none()
    
    # остальные методы (update, delete, get_by_filter) аналогичны предыдущим репозиториям