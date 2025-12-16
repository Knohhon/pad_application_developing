from uuid import UUID

import pytest
from app.models.database_models import User
from app.repositories.user_repository import UserRepository
from sqlalchemy.ext.asyncio import AsyncSession


class TestUserRepository:

    @pytest.mark.asyncio
    async def test_delete_user(
        self, session: AsyncSession, user_repository: UserRepository
    ):
        """Тест удаления пользователя"""
        from app.schemas.user import UserCreate

        user_data = UserCreate(
            email="delete@example.com", username="delete_user", description="Test user"
        )

        user = await user_repository.create(session=session, user_data=user_data)

        await user_repository.delete(session=session, user_id=user.id)

        deleted_user = await user_repository.get_by_id(session=session, user_id=user.id)
        assert deleted_user is None

    @pytest.mark.asyncio
    async def test_get_users_list(
        self, session: AsyncSession, user_repository: UserRepository
    ):
        """Тест получения списка пользователей"""
        from app.schemas.user import UserCreate

        users_data = [
            UserCreate(email="list1@example.com", username="user1"),
            UserCreate(email="list2@example.com", username="user2"),
            UserCreate(email="list3@example.com", username="user3"),
        ]

        for user_data in users_data:
            await user_repository.create(session=session, user_data=user_data)

        users = await user_repository.get_by_filter(session=session, count=10, page=1)

        assert len(users) >= 3
        usernames = [user.username for user in users]
        assert "user1" in usernames
        assert "user2" in usernames
        assert "user3" in usernames
