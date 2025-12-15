import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID
from app.services.user_service import UserService
from app.schemas.user import UserCreate, UserUpdate
from app.models.database_models import User, Order
from decimal import Decimal
from app.repositories.user_repository import UserRepository
from datetime import datetime

class TestUserService:
    @pytest.mark.asyncio
    async def test_create_user_success(self):
        """Тест успешного создания пользователя"""
        mock_repo = AsyncMock(spec=UserRepository)
        mock_repo.create.return_value = User(
            id=UUID("12345678-1234-5678-1234-567812345678"),
            username="valid_user",
            email="valid@example.com",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        user_service = UserService(mock_repo)
        
        user_data = UserCreate(
            username="valid_user",
            email="valid@example.com",
            description="Test user"
        )
        
        user = await user_service.create(MagicMock(), user_data)
        
        mock_repo.create.assert_called_once()
        assert user.username == "valid_user"
        assert user.email == "valid@example.com"

    @pytest.mark.asyncio
    async def test_create_user_invalid_username(self):
        """Тест создания пользователя с коротким username"""
        mock_repo = AsyncMock(spec=UserRepository)
        user_service = UserService(mock_repo)


        user_data = UserCreate.model_construct(
            username="ab",
            email="valid@example.com"
        )

        with pytest.raises(ValueError, match="Username must be at least 3 characters long"):
            await user_service.create(MagicMock(), user_data)


        mock_repo.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_user_invalid_email(self):
        """Тест создания пользователя с некорректным email"""
        mock_repo = AsyncMock(spec=UserRepository)
        user_service = UserService(mock_repo)
        
        user_data = UserCreate.model_construct(
            username="valid_user",
            email="invalid-email"
        )
        
        with pytest.raises(ValueError, match="Invalid email format"):
            await user_service.create(MagicMock(), user_data)
        
        mock_repo.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_user_success(self):
        """Тест успешного обновления пользователя"""
        mock_repo = AsyncMock(spec=UserRepository)
        mock_repo.update.return_value = User(
            id=UUID("12345678-1234-5678-1234-567812345678"),
            username="updated_user",
            email="original@example.com",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        user_service = UserService(mock_repo)
        
        update_data = UserUpdate(username="updated_user")
        user = await user_service.update(
            MagicMock(), 
            UUID("12345678-1234-5678-1234-567812345678"), 
            update_data
        )
        
        mock_repo.update.assert_called_once()
        assert user.username == "updated_user"

    @pytest.mark.asyncio
    async def test_update_user_invalid_username(self):
        """Тест обновления с коротким username"""
        mock_repo = AsyncMock(spec=UserRepository)
        user_service = UserService(mock_repo)
        
        update_data = UserUpdate.model_construct(username="ab")
        
        with pytest.raises(ValueError, match="Username must be at least 3 characters long"):
            await user_service.update(
                MagicMock(), 
                UUID("12345678-1234-5678-1234-567812345678"), 
                update_data
            )
        
        mock_repo.update.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_user_cannot_change_email(self):
        """Тест попытки изменения email (запрещено)"""
        mock_repo = AsyncMock(spec=UserRepository)
        user_service = UserService(mock_repo)

        mock_user = MagicMock(spec=User)
        mock_user.id = UUID("12345678-1234-5678-1234-567812345678")
        mock_user.email = "original@example.com"
        mock_user.username = "test_user"

        mock_repo.get_by_id.return_value = mock_user

        update_data = UserUpdate.model_construct(
            email="new@example.com"
        )

        with pytest.raises(ValueError, match="Email cannot be changed after registration"):
            await user_service.update(
                session=MagicMock(),
                user_id=mock_user.id,
                user_data=update_data
            )

        mock_repo.update.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_user_with_orders(self):
        """Тест удаления пользователя с существующими заказами"""
        mock_repo = AsyncMock(spec=UserRepository)
        
        user = User(
            id=UUID("12345678-1234-5678-1234-567812345678"),
            username="user_with_orders",
            email="has_orders@example.com",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            orders=[Order(id=UUID("87654321-4321-8765-4321-876543210987"))]
        )
        mock_repo.get_by_id.return_value = user
        
        user_service = UserService(mock_repo)
        
        with pytest.raises(ValueError, match="Cannot delete user with existing orders"):
            await user_service.delete(
                MagicMock(), 
                UUID("12345678-1234-5678-1234-567812345678")
            )
        
        mock_repo.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_user_success(self):
        """Тест успешного удаления пользователя без заказов"""
        mock_repo = AsyncMock(spec=UserRepository)
        
        user = User(
            id=UUID("12345678-1234-5678-1234-567812345678"),
            username="no_orders",
            email="no_orders@example.com",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            orders=[]
        )
        mock_repo.get_by_id.return_value = user
        
        user_service = UserService(mock_repo)
        
        await user_service.delete(
            MagicMock(), 
            UUID("12345678-1234-5678-1234-567812345678")
        )
        
        mock_repo.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_filter_invalid_count(self):
        """Тест фильтрации с некорректным count"""
        mock_repo = AsyncMock(spec=UserRepository)
        user_service = UserService(mock_repo)
        
        with pytest.raises(ValueError, match="Count must be between 1 and 100"):
            await user_service.get_by_filter(MagicMock(), count=0)
        
        with pytest.raises(ValueError, match="Count must be between 1 and 100"):
            await user_service.get_by_filter(MagicMock(), count=101)
        
        mock_repo.get_by_filter.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_by_filter_invalid_page(self):
        """Тест фильтрации с некорректным page"""
        mock_repo = AsyncMock(spec=UserRepository)
        user_service = UserService(mock_repo)
        
        with pytest.raises(ValueError, match="Page must be greater than 0"):
            await user_service.get_by_filter(MagicMock(), page=0)
        
        mock_repo.get_by_filter.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_by_filter_success(self):
        """Тест успешной фильтрации пользователей"""
        mock_repo = AsyncMock(spec=UserRepository)
        mock_repo.get_by_filter.return_value = [
            User(
                id=UUID("12345678-1234-5678-1234-567812345678"),
                username="test1",
                email="test1@example.com",
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        ]

        user_service = UserService(mock_repo)

        mock_session = MagicMock()

        users = await user_service.get_by_filter(
            mock_session, 
            count=10,
            page=1,
            username="test1"
        )

        mock_repo.get_by_filter.assert_called_once_with(
            mock_session, 
            count=10,
            page=1,
            username="test1"
        )

        assert len(users) == 1
        assert users[0].username == "test1"