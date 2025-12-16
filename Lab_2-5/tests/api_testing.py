from typing import Any, Dict
from uuid import UUID

import pytest
from app.models.database_models import User
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from httpx import AsyncClient
from litestar import Provide, delete, get, post, put
from litestar.status_codes import (HTTP_200_OK, HTTP_201_CREATED,
                                   HTTP_404_NOT_FOUND,
                                   HTTP_422_UNPROCESSABLE_ENTITY)
from litestar.testing import create_test_client
from polyfactory.factories.pydantic_factory import ModelFactory
from pydantic import BaseModel


class UserResponseFactory(ModelFactory[UserResponse]):
    __model__ = UserResponse


class UserCreateFactory(ModelFactory[UserCreate]):
    __model__ = UserCreate


class UserUpdateFactory(ModelFactory[UserUpdate]):
    __model__ = UserUpdate


@pytest.fixture
def user_response() -> UserResponse:
    return UserResponseFactory.build()


@pytest.fixture
def user_create_data() -> UserCreate:
    return UserCreateFactory.build()


@pytest.fixture
def user_update_data() -> UserUpdate:
    return UserUpdateFactory.build()


class MockUserService:
    def __init__(self, user_response: UserResponse = None):
        self.user_response = user_response

    async def get_by_id(self, session: Any, user_id: UUID) -> UserResponse:
        if self.user_response:
            return self.user_response
        raise ValueError("User not found")

    async def create(self, session: Any, user_data: UserCreate) -> UserResponse:
        return UserResponse(
            id=UUID("12345678-1234-5678-1234-567812345678"), **user_data.model_dump()
        )

    async def update(
        self, session: Any, user_id: UUID, user_data: UserUpdate
    ) -> UserResponse:
        if self.user_response:
            update_data = user_data.model_dump(exclude_unset=True)
            return UserResponse(
                id=user_id,
                **self.user_response.model_dump(exclude={"id"}),
                **update_data,
            )
        raise ValueError("User not found")

    async def delete(self, session: Any, user_id: UUID) -> None:
        return


@get(path="/users/{user_id:uuid}")
async def get_user(user_id: UUID, service: MockUserService) -> UserResponse:
    return await service.get_by_id(None, user_id)


@post(path="/users")
async def create_user(data: UserCreate, service: MockUserService) -> UserResponse:
    return await service.create(None, data)


@put(path="/users/{user_id:uuid}")
async def update_user(
    user_id: UUID, data: UserUpdate, service: MockUserService
) -> UserResponse:
    return await service.update(None, user_id, data)


@delete(path="/users/{user_id:uuid}")
async def delete_user(user_id: UUID, service: MockUserService) -> None:
    await service.delete(None, user_id)


def test_get_user_endpoint(user_response: UserResponse):
    """Тест получения пользователя по ID"""
    with create_test_client(
        route_handlers=[get_user],
        dependencies={
            "service": Provide(lambda: MockUserService(user_response=user_response))
        },
    ) as client:
        response = client.get(f"/users/{user_response.id}")
        assert response.status_code == HTTP_200_OK
        assert response.json() == user_response.model_dump(mode="json")


def test_get_user_not_found():
    """Тест обработки несуществующего пользователя"""
    with create_test_client(
        route_handlers=[get_user],
        dependencies={"service": Provide(lambda: MockUserService(user_response=None))},
    ) as client:
        response = client.get("/users/12345678-1234-5678-1234-567812345678")
        assert response.status_code == HTTP_404_NOT_FOUND
        assert "User not found" in response.json()["detail"]


def test_create_user_endpoint(user_create_data: UserCreate):
    """Тест создания пользователя"""
    with create_test_client(
        route_handlers=[create_user],
        dependencies={"service": Provide(lambda: MockUserService())},
    ) as client:
        response = client.post("/users", json=user_create_data.model_dump())
        assert response.status_code == HTTP_201_CREATED
        created_user = response.json()
        assert created_user["username"] == user_create_data.username
        assert created_user["email"] == user_create_data.email


def test_create_user_invalid_data():
    """Тест обработки невалидных данных при создании"""
    with create_test_client(
        route_handlers=[create_user],
        dependencies={"service": Provide(lambda: MockUserService())},
    ) as client:
        invalid_data = {"username": "ab", "email": "invalid-email"}
        response = client.post("/users", json=invalid_data)
        assert response.status_code == HTTP_422_UNPROCESSABLE_ENTITY
        errors = response.json()["detail"]
        assert any("Username must be at least 3 characters" in e["msg"] for e in errors)
        assert any("Invalid email format" in e["msg"] for e in errors)


def test_update_user_endpoint(
    user_response: UserResponse, user_update_data: UserUpdate
):
    """Тест обновления пользователя"""
    with create_test_client(
        route_handlers=[update_user],
        dependencies={
            "service": Provide(lambda: MockUserService(user_response=user_response))
        },
    ) as client:
        response = client.put(
            f"/users/{user_response.id}",
            json=user_update_data.model_dump(exclude_unset=True),
        )
        assert response.status_code == HTTP_200_OK
        updated = response.json()

        for field, value in user_update_data.model_dump(exclude_unset=True).items():
            assert updated[field] == value


def test_update_user_invalid_data(user_response: UserResponse):
    """Тест обработки невалидных данных при обновлении"""
    with create_test_client(
        route_handlers=[update_user],
        dependencies={
            "service": Provide(lambda: MockUserService(user_response=user_response))
        },
    ) as client:
        invalid_data = {"username": "ab"}
        response = client.put(f"/users/{user_response.id}", json=invalid_data)
        assert response.status_code == HTTP_422_UNPROCESSABLE_ENTITY
        errors = response.json()["detail"]
        assert any("Username must be at least 3 characters" in e["msg"] for e in errors)


def test_delete_user_endpoint(user_response: UserResponse):
    """Тест удаления пользователя"""
    with create_test_client(
        route_handlers=[delete_user],
        dependencies={
            "service": Provide(lambda: MockUserService(user_response=user_response))
        },
    ) as client:
        response = client.delete(f"/users/{user_response.id}")
        assert response.status_code == HTTP_200_OK
        assert response.json() == {"status": "success", "message": "User deleted"}


def test_delete_user_not_found():
    """Тест удаления несуществующего пользователя"""
    with create_test_client(
        route_handlers=[delete_user],
        dependencies={"service": Provide(lambda: MockUserService(user_response=None))},
    ) as client:
        response = client.delete("/users/12345678-1234-5678-1234-567812345678")
        assert response.status_code == HTTP_404_NOT_FOUND
        assert "User not found" in response.json()["detail"]
