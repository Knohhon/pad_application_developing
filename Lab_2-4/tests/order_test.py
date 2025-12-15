# tests/order_test.py
import pytest
from decimal import Decimal
from app.schemas.order import OrderCreate, OrderItemCreate
from app.schemas.product import ProductCreate
from app.schemas.user import UserCreate
from app.schemas.address import AddressCreate

@pytest.mark.asyncio
async def test_create_order_with_multiple_products(
    session,  # <-- Получаем сессию напрямую из фикстуры
    order_repository,
    user_repository,
    address_repository,
    product_repository
):
    """Тест создания заказа с несколькими продуктами"""
    # 1. Создаем пользователя
    user = await user_repository.create(
        session=session,  # <-- Передаем реальную сессию
        user_data=UserCreate(
            email="order@example.com",
            username="order_user",
            description="Test user"
        )
    )

    # 2. Создаем адрес
    address = await address_repository.create(
        session=session,  # <-- Передаем реальную сессию
        address_data=AddressCreate(
            user_id=user.id,
            street="123 Test St",
            city="Test City",
            state="CA",
            zip_code="12345",
            country="USA"
        )
    )

    # 3. Создаем продукты
    product1 = await product_repository.create(
        session=session,  # <-- Передаем реальную сессию
        product_data=ProductCreate(
            label="Product 1",
            count_in_package=10,
            count_in_warehouse=100,
            price=Decimal("10.00")
        )
    )
    
    product2 = await product_repository.create(
        session=session,  # <-- Передаем реальную сессию
        product_data=ProductCreate(
            label="Product 2",
            count_in_package=5,
            count_in_warehouse=50,
            price=Decimal("15.50")
        )
    )

    # 4. Создаем заказ с несколькими позициями
    order_data = OrderCreate(
        user_id=user.id,
        address_id=address.id,
        items=[
            OrderItemCreate(product_id=product1.id, quantity=2),
            OrderItemCreate(product_id=product2.id, quantity=3)
        ]
    )
    
    order = await order_repository.create(
        session=session,  # <-- Передаем реальную сессию
        order_data=order_data
    )

    # 5. Проверяем основные данные заказа
    assert order.id is not None
    assert order.user_id == user.id
    assert order.address_id == address.id
    assert len(order.items) == 2

    # 6. Проверяем позиции заказа
    items = order.items
    item1 = next(i for i in items if i.product_id == product1.id)
    item2 = next(i for i in items if i.product_id == product2.id)
    
    assert item1.quantity == 2
    assert item1.unit_price == Decimal("10.00")
    assert item2.quantity == 3
    assert item2.unit_price == Decimal("15.50")

    # 7. Проверяем остатки на складе
    updated_product1 = await product_repository.get_by_id(
        session=session,  # <-- Передаем реальную сессию
        product_id=product1.id
    )
    updated_product2 = await product_repository.get_by_id(
        session=session,  # <-- Передаем реальную сессию
        product_id=product2.id
    )
    
    assert updated_product1.count_in_warehouse == 98
    assert updated_product2.count_in_warehouse == 47