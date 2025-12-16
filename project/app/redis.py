import redis
from typing import Optional, Any, Union
from datetime import timedelta
import json
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.user import UserCreate, UserUpdate
from app.schemas.product import ProductCreate, ProductUpdate

class RedisCache:
    def __init__(self, host: str = 'localhost', port: int = 6379, db: int = 0):
        """Инициализация подключения к Redis"""
        self.client = redis.Redis(
            host=host,
            port=port,
            db=db,
            decode_responses=True,
            socket_timeout=5,
            socket_connect_timeout=5
        )
        self._test_connection()
    
    def _test_connection(self):
        """Проверка подключения к Redis"""
        try:
            self.client.ping()
            print("Успешное подключение к Redis")
        except redis.ConnectionError as e:
            print(f"Ошибка подключения к Redis: {e}")
            raise
    
    def _serialize(self, data: Any) -> str:
        """Сериализация данных в JSON"""
        if isinstance(data, dict):
            return json.dumps(data, default=str)
        return str(data)
    
    def _deserialize(self, data: str) -> Any:
        """Десериализация данных из JSON"""
        try:
            return json.loads(data)
        except (json.JSONDecodeError, TypeError):
            return data
    
    def set_user(self, user_id: UUID, user_data: dict, expire: timedelta = timedelta(hours=1)):
        """Сохранение данных пользователя в кэш с TTL 1 час"""
        key = f"user:{user_id}"
        self.client.setex(key, int(expire.total_seconds()), self._serialize(user_data))
    
    def get_user(self, user_id: UUID) -> Optional[dict]:
        """Получение данных пользователя из кэша"""
        key = f"user:{user_id}"
        data = self.client.get(key)
        return self._deserialize(data) if data else None
    
    def delete_user(self, user_id: UUID):
        """Удаление данных пользователя из кэша"""
        key = f"user:{user_id}"
        self.client.delete(key)
    
    def set_product(self, product_id: UUID, product_data: dict, expire: timedelta = timedelta(minutes=10)):
        """Сохранение данных продукта в кэш с TTL 10 минут"""
        key = f"product:{product_id}"
        self.client.setex(key, int(expire.total_seconds()), self._serialize(product_data))
    
    def get_product(self, product_id: UUID) -> Optional[dict]:
        """Получение данных продукта из кэша"""
        key = f"product:{product_id}"
        data = self.client.get(key)
        return self._deserialize(data) if data else None
    
    def update_product(self, product_id: UUID, product_data: dict):
        """Обновление данных продукта в кэше"""
        self.set_product(product_id, product_data)
    
    def delete_product(self, product_id: UUID):
        """Удаление данных продукта из кэша"""
        key = f"product:{product_id}"
        self.client.delete(key)
    
    def close(self):
        """Закрытие соединения с Redis"""
        if self.client:
            self.client.close()
            print("Соединение с Redis закрыто")

# Интеграция в сервисы приложения
from app.services.user_service import UserService
from app.services.product_service import ProductService
from app.repositories.user_repository import UserRepository
from app.repositories.product_repository import ProductRepository

class CachingUserService(UserService):
    def __init__(self, user_repository: UserRepository, cache: RedisCache):
        super().__init__(user_repository)
        self.cache = cache
    
    async def get_by_id(self, session: AsyncSession, user_id: UUID) -> Optional[dict]:
        """Получение пользователя с использованием кэша"""
        # Сначала пробуем получить из кэша
        cached_user = self.cache.get_user(user_id)
        if cached_user:
            return cached_user
        
        # Если нет в кэше, получаем из БД
        user = await super().get_by_id(session, user_id)
        if user:
            # Сохраняем в кэш
            user_dict = self._user_to_dict(user)
            self.cache.set_user(user_id, user_dict)
            return user_dict
        return None
    
    async def update(self, session: AsyncSession, user_id: UUID, user_data: UserUpdate) -> dict:
        """Обновление пользователя с очисткой кэша"""
        # Обновляем в БД
        updated_user = await super().update(session, user_id, user_data)
        
        # Очищаем кэш
        self.cache.delete_user(user_id)
        
        # Возвращаем обновленные данные
        return self._user_to_dict(updated_user)
    
    def _user_to_dict(self, user: Any) -> dict:
        """Преобразование объекта пользователя в словарь"""
        return {
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "description": user.description,
            "created_at": user.created_at.isoformat(),
            "updated_at": user.updated_at.isoformat()
        }

class CachingProductService(ProductService):
    def __init__(self, product_repository: ProductRepository, cache: RedisCache):
        super().__init__(product_repository)
        self.cache = cache
    
    async def get_by_id(self, session: AsyncSession, product_id: UUID) -> Optional[dict]:
        """Получение продукта с использованием кэша"""
        # Сначала пробуем получить из кэша
        cached_product = self.cache.get_product(product_id)
        if cached_product:
            return cached_product
        
        # Если нет в кэше, получаем из БД
        product = await super().get_by_id(session, product_id)
        if product:
            # Сохраняем в кэш
            product_dict = self._product_to_dict(product)
            self.cache.set_product(product_id, product_dict)
            return product_dict
        return None
    
    async def update(self, session: AsyncSession, product_id: UUID, product_data: ProductUpdate) -> dict:
        """Обновление продукта с обновлением кэша"""
        # Обновляем в БД
        updated_product = await super().update(session, product_id, product_data)
        
        # Обновляем кэш
        product_dict = self._product_to_dict(updated_product)
        self.cache.update_product(product_id, product_dict)
        
        return product_dict
    
    def _product_to_dict(self, product: Any) -> dict:
        """Преобразование объекта продукта в словарь"""
        return {
            "id": str(product.id),
            "label": product.label,
            "count_in_package": product.count_in_package,
            "count_in_warehouse": product.count_in_warehouse,
            "price": str(product.price),
            "created_at": product.created_at.isoformat(),
            "updated_at": product.updated_at.isoformat()
        }

# Инициализация в основном приложении
from litestar import Litestar
from litestar.di import Provide

# Создаем экземпляр кэша
redis_cache = RedisCache(host="localhost", port=6379, db=0)

async def get_cache() -> RedisCache:
    return redis_cache

def create_app() -> Litestar:

    user_repository = UserRepository()
    product_repository = ProductRepository()
    
    user_service = CachingUserService(user_repository, redis_cache)
    product_service = CachingProductService(product_repository, redis_cache)
    
    app = Litestar(
        route_handlers=[...],
        dependencies={
            "user_service": Provide(lambda: user_service),
            "product_service": Provide(lambda: product_service),
            "cache": Provide(get_cache)
        },
        on_shutdown=[lambda: redis_cache.close()]
    )
    return app