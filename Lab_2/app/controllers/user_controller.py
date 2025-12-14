from typing import List, Optional
from uuid import UUID
from litestar import Controller, get, post, delete, put
from litestar.exceptions import NotFoundException, ValidationException, InternalServerException
from litestar.params import Parameter
from litestar.status_codes import HTTP_201_CREATED, HTTP_204_NO_CONTENT
from sqlalchemy.ext.asyncio import AsyncSession
from services.user_service import UserService
from schemas.user import UserCreate, UserUpdate, UserResponse

class UserController(Controller):
    path = "/users"
    tags = ["Users"]

    @get("/{user_id:uuid}")
    async def get_user_by_id(
        self,
        user_service: UserService,
        session: AsyncSession,
        user_id: UUID,
    ) -> UserResponse:
        """Получить пользователя по ID"""
        user = await user_service.get_by_id(session, user_id)
        if not user:
            raise NotFoundException(detail=f"User with ID {user_id} not found")
        return UserResponse.model_validate(user)

    @get()
    async def get_all_users(
        self,
        user_service: UserService,
        session: AsyncSession,
        count: Optional[int] = Parameter(default=10, ge=1, le=100),
        page: Optional[int] = Parameter(default=1, ge=1),
        username: Optional[str] = None,
        email: Optional[str] = None,
    ) -> List[UserResponse]:
        """Получить список пользователей с пагинацией и фильтрацией"""
        filters = {}
        if username:
            filters["username"] = username
        if email:
            filters["email"] = email
            
        users = await user_service.get_by_filter(
            session,
            count=count,
            page=page,
            **filters
        )
        return [UserResponse.model_validate(user) for user in users]

    @post(status_code=HTTP_201_CREATED)
    async def create_user(
        self,
        user_service: UserService,
        session: AsyncSession,
        user_data: UserCreate,
    ) -> UserResponse:
        """Создать нового пользователя"""
        try:
            user = await user_service.create(session, user_data)
            return UserResponse.model_validate(user)
        except ValueError as e:
            raise ValidationException(detail=str(e))
        except Exception as e:
            await session.rollback()
            raise InternalServerException(detail="Failed to create user")

    @delete("/{user_id:uuid}", status_code=HTTP_204_NO_CONTENT)
    async def delete_user(
        self,
        user_service: UserService,
        session: AsyncSession,
        user_id: UUID,
    ) -> None:
        """Удалить пользователя"""
        try:
            await user_service.delete(session, user_id)
            return None
        except ValueError as e:
            raise NotFoundException(detail=str(e))
        except Exception as e:
            await session.rollback()
            raise InternalServerException(detail="Failed to delete user")

    @put("/{user_id:uuid}")
    async def update_user(
        self,
        user_service: UserService,
        session: AsyncSession,
        user_id: UUID,
        user_data: UserUpdate,
    ) -> UserResponse:
        """Обновить данные пользователя"""
        try:
            user = await user_service.update(session, user_id, user_data)
            return UserResponse.model_validate(user)
        except ValueError as e:
            if "not found" in str(e).lower():
                raise NotFoundException(detail=str(e))
            raise ValidationException(detail=str(e))
        except Exception as e:
            await session.rollback()
            raise InternalServerException(detail="Failed to update user")