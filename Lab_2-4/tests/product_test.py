import pytest
from uuid import UUID
from decimal import Decimal
from app.models.database_models import Product
from app.repositories.product_repository import ProductRepository
from app.schemas.product import ProductCreate, ProductUpdate
from sqlalchemy.ext.asyncio import AsyncSession

class TestProductRepository:
    @pytest.mark.asyncio
    async def test_create_product(self, session: AsyncSession, product_repository: ProductRepository):
        """Тест создания продукта с ценой"""
        product_data = ProductCreate(
            label="Test Product",
            count_in_package=10,
            count_in_warehouse=100,
            price=Decimal("19.99")
        )
        
        product = await product_repository.create(session=session, product_data=product_data)
        
        assert product.id is not None
        assert product.label == "Test Product"
        assert product.price == Decimal("19.99")
        assert product.count_in_warehouse == 100

    @pytest.mark.asyncio
    async def test_get_product_by_id(self, session: AsyncSession, product_repository: ProductRepository):
        """Тест получения продукта по ID"""
        product_data = ProductCreate(
            label="Find Me",
            count_in_package=5,
            count_in_warehouse=50,
            price=Decimal("25.50")
        )
        product = await product_repository.create(session=session, product_data=product_data)
        
        found_product = await product_repository.get_by_id(session=session, product_id=product.id)
        assert found_product is not None
        assert found_product.label == "Find Me"
        assert found_product.price == Decimal("25.50")


    @pytest.mark.asyncio
    async def test_update_product(self, session, product_repository):
        """Тест обновления продукта"""
        # Создаем исходный продукт
        product_data = ProductCreate(
            label="Original",
            count_in_package=10,
            count_in_warehouse=100,
            price=Decimal("10.00")
        )
        product = await product_repository.create(session, product_data)
        original_updated_at = product.updated_at

        # Создаем объект ProductUpdate
        update_data = ProductUpdate(
            label="Updated Product",
            price=Decimal("15.99"),
            count_in_warehouse=150
        )

        # Обновляем продукт
        updated = await product_repository.update(session, product.id, update_data)

        # Проверки основных полей
        assert updated.label == "Updated Product"
        assert updated.price == Decimal("15.99")
        assert updated.count_in_warehouse == 150
        
        # Более надежная проверка обновления времени
        # 1. Проверяем, что updated_at изменился
        assert updated.updated_at != original_updated_at
        
        # 2. Проверяем, что время обновления больше или равно исходному
        # (учитываем возможную погрешность в миллисекундах)
        time_difference = updated.updated_at - original_updated_at
        assert time_difference.total_seconds() >= 0
        
        # 3. Проверяем, что время обновления разумное (не больше 5 секунд)
        assert time_difference.total_seconds() < 5.0
        
    @pytest.mark.asyncio
    async def test_get_products_list(self, session: AsyncSession, product_repository: ProductRepository):
        """Тест получения списка продуктов"""
        products_data = [
            ProductCreate(label="Product A", count_in_package=5, count_in_warehouse=20, price=Decimal("5.99")),
            ProductCreate(label="Product B", count_in_package=10, count_in_warehouse=30, price=Decimal("9.99")),
            ProductCreate(label="Product C", count_in_package=15, count_in_warehouse=40, price=Decimal("12.50"))
        ]
        
        for data in products_data:
            await product_repository.create(session=session, product_data=data)
        
        products = await product_repository.get_by_filter(session=session, count=10, page=1)
        assert len(products) >= 3
        
        labels = [p.label for p in products]
        assert "Product A" in labels
        assert "Product B" in labels
        assert "Product C" in labels

    @pytest.mark.asyncio
    async def test_delete_product(self, session: AsyncSession, product_repository: ProductRepository):
        """Тест удаления продукта"""
        product_data = ProductCreate(
            label="Delete Me",
            count_in_package=5,
            count_in_warehouse=10,
            price=Decimal("7.99")
        )
        product = await product_repository.create(session=session, product_data=product_data)
        
        await product_repository.delete(session=session, product_id=product.id)
        
        # Проверяем, что продукт удален
        deleted = await product_repository.get_by_id(session=session, product_id=product.id)
        assert deleted is None