# app/main.py
import datetime
import os
from typing import AsyncGenerator

from app.controllers.user_controller import UserController
from app.repositories.user_repository import UserRepository
from app.services.user_service import UserService
from litestar import Litestar, get
from litestar.config.cors import CORSConfig
from litestar.di import Provide
from litestar.exceptions import HTTPException
from litestar.logging import LoggingConfig
from litestar.openapi.config import OpenAPIConfig
from litestar.openapi.spec import Contact, Tag
from litestar.status_codes import HTTP_500_INTERNAL_SERVER_ERROR
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_async_engine(DATABASE_URL, echo=True)
async_session_factory = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def provide_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Провайдер сессии базы данных"""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise HTTPException(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database operation failed",
            ) from e
        finally:
            await session.close()


def provide_user_repository() -> UserRepository:
    """Провайдер репозитория пользователей"""
    return UserRepository()


def provide_user_service() -> UserService:
    """Провайдер сервиса пользователей"""
    return UserService(provide_user_repository())


@get("/health")
async def health_check() -> dict:
    """Эндпоинт для проверки состояния приложения"""
    return {"status": "healthy", "timestamp": datetime.datetime.utcnow().isoformat()}


async def on_startup() -> None:
    """Действия при запуске приложения"""
    print("Application starting up...")


async def on_shutdown() -> None:
    """Действия при остановке приложения"""
    await engine.dispose()
    print("Application shutting down...")


# Конфигурация логирования
logging_config = LoggingConfig(
    loggers={
        "app": {
            "level": "INFO",
            "handlers": ["console"],
        }
    }
)

app = Litestar(
    route_handlers=[
        UserController,
        health_check,
    ],
    dependencies={
        "session": Provide(provide_db_session),
        "user_repository": Provide(provide_user_repository),
        "user_service": Provide(provide_user_service),
    },
    on_startup=[on_startup],
    on_shutdown=[on_shutdown],
    logging_config=logging_config,
    debug=os.getenv("DEBUG", "False").lower() == "true",
    openapi_config=OpenAPIConfig(
        title="User Management API",
        version="1.0.0",
        description="API for managing users with their addresses and orders",
        contact=Contact(name="API Support", email="support@example.com"),
        tags=[
            Tag(name="Users", description="User management operations"),
        ],
    ),
    cors_config=CORSConfig(
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    ),
)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
        reload=os.getenv("RELOAD", "False").lower() == "true",
    )
