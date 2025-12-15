from typing import Optional, List, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserUpdate
from app.models.database_models import User

class UserService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def get_by_id(self, session: AsyncSession, user_id: UUID) -> Optional[User]:
        """Получить пользователя по ID с предзагрузкой связанных данных"""
        return await self.user_repository.get_by_id(session, user_id)

    async def get_by_filter(
        self,
        session: AsyncSession,
        count: int = 10,
        page: int = 1,
        **kwargs: Any
    ) -> List[User]:
        """Получить список пользователей с фильтрацией и пагинацией"""
        if count < 1 or count > 100:
            raise ValueError("Count must be between 1 and 100")
        if page < 1:
            raise ValueError("Page must be greater than 0")
        
        return await self.user_repository.get_by_filter(
            session,
            count=count,
            page=page,
            **kwargs
        )

    async def create(self, session: AsyncSession, user_data: UserCreate) -> User:
        """Создать нового пользователя с бизнес-валидацией"""
        if len(user_data.username) < 3:
            raise ValueError("Username must be at least 3 characters long")
        if "@" not in user_data.email:
            raise ValueError("Invalid email format")
        
        return await self.user_repository.create(session, user_data)

    async def update(
        self,
        session: AsyncSession,
        user_id: UUID,
        user_data: UserUpdate
    ) -> User:
        """Обновить данные пользователя с бизнес-правилами"""
        if user_data.username and len(user_data.username) < 3:
            raise ValueError("Username must be at least 3 characters long")
        
        if hasattr(user_data, 'email') and user_data.email is not None:
            raise ValueError("Email cannot be changed after registration")
        
        return await self.user_repository.update(session, user_id, user_data)

    async def delete(self, session: AsyncSession, user_id: UUID) -> None:
        """Удалить пользователя с проверкой бизнес-правил"""
        user = await self.get_by_id(session, user_id)
        if not user:
            raise ValueError(f"User with id {user_id} not found")
        
        if any(order for order in user.orders):
            raise ValueError("Cannot delete user with existing orders")
        
        await self.user_repository.delete(session, user_id)