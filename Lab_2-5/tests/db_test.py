import os

import pytest
from app.models.database_models import Base
from litestar.testing import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

from app.main import app
from app.repositories.address_repository import AddressRepository
from app.repositories.order_repository import OrderRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.user_repository import UserRepository


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session")
async def engine():
    """Создаёт тестовый движок базы данных"""
    return create_async_engine(
        os.environ["DATABASE_URL"],
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


@pytest.fixture(scope="session")
async def tables(engine):
    """Создаёт и удаляет таблицы в тестовой базе"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def session(engine, tables):
    """Создаёт асинхронную сессию для тестов"""
    async_session_factory = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.rollback()


@pytest.fixture
async def user_repository(session):
    return UserRepository()


@pytest.fixture
async def product_repository(session):
    return ProductRepository()


@pytest.fixture
async def order_repository(session):
    return OrderRepository()


@pytest.fixture
async def address_repository(session):
    return AddressRepository()


@pytest.fixture
def client():
    return TestClient(app=app)
