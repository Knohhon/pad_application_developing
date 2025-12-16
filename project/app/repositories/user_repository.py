from typing import Any, List, Optional
from uuid import UUID

from app.models.database_models import User
from app.schemas.user import UserCreate, UserUpdate
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


class UserRepository:
    async def get_by_id(self, session: AsyncSession, user_id: UUID) -> Optional[User]:
        """Получить пользователя по UUID с предзагрузкой связанных данных"""
        result = await session.execute(
            select(User)
            .options(selectinload(User.addresses), selectinload(User.orders))
            .where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_filter(
        self, session: AsyncSession, count: int = 10, page: int = 1, **kwargs: Any
    ) -> List[User]:
        """Получить список пользователей с фильтрацией, пагинацией и предзагрузкой связей"""
        query = select(User).options(
            selectinload(User.addresses), selectinload(User.orders)
        )

        for key, value in kwargs.items():
            if hasattr(User, key) and value is not None:
                query = query.where(getattr(User, key) == value)

        offset = (page - 1) * count if page > 0 else 0
        query = query.offset(offset).limit(count)

        result = await session.execute(query)
        return list(result.scalars().all())

    async def create(self, session: AsyncSession, user_data: UserCreate) -> User:
        """Создать нового пользователя с автоматической генерацией UUID"""
        user_dict = user_data.model_dump(exclude_unset=True, exclude={"id"})

        new_user = User(**user_dict)

        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)

        return new_user

    async def update(
        self, session: AsyncSession, user_id: UUID, user_data: UserUpdate
    ) -> User:
        """Обновить данные пользователя с автоматическим обновлением updated_at"""
        user = await self.get_by_id(session, user_id)
        if not user:
            raise ValueError(f"User with id {user_id} not found")

        update_data = user_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(user, field) and value is not None:
                setattr(user, field, value)

        session.add(user)
        await session.commit()
        await session.refresh(user)

        return user

    async def delete(self, session: AsyncSession, user_id: UUID) -> None:
        """Удалить пользователя и связанные данные (каскадное удаление настроено в БД)"""
        user = await self.get_by_id(session, user_id)
        if not user:
            raise ValueError(f"User with id {user_id} not found")

        await session.delete(user)
        await session.commit()
