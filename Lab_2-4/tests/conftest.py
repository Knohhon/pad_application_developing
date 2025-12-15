# tests/conftest.py
import pytest
import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.models.database_models import Base

# Настраиваем тестовую БД
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

# Импортируем приложение и репозитории ПОСЛЕ настройки переменных окружения
from app.main import app
from app.repositories.user_repository import UserRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.order_repository import OrderRepository
from app.repositories.address_repository import AddressRepository

@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"

@pytest.fixture(scope="session")
async def engine():
    return create_async_engine(
        os.environ["DATABASE_URL"],
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

@pytest.fixture(scope="session")
async def tables(engine):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def session(engine, tables):
    """Фикстура сессии, доступная во всех тестах"""
    async_session_factory = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.rollback()

# Фикстуры репозиториев НЕ принимают сессию в конструкторе
@pytest.fixture
def user_repository():
    return UserRepository()

@pytest.fixture
def product_repository():
    return ProductRepository()

@pytest.fixture
def order_repository():
    return OrderRepository()

@pytest.fixture
def address_repository():
    return AddressRepository()

@pytest.fixture
def client():
    from litestar.testing import TestClient
    return TestClient(app=app)