from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, field_validator


class AddressBase(BaseModel):
    street: str
    city: str
    state: Optional[str] = None
    zip_code: str
    country: str
    is_primary: bool = False

    @field_validator("street")
    @classmethod
    def validate_street(cls, v: str) -> str:
        """Валидация улицы"""
        if not v.strip():
            raise ValueError("Street cannot be empty")
        if len(v) > 100:
            raise ValueError("Street name is too long")
        return v.strip()

    @field_validator("city")
    @classmethod
    def validate_city(cls, v: str) -> str:
        """Валидация города"""
        if not v.strip():
            raise ValueError("City cannot be empty")
        if len(v) > 50:
            raise ValueError("City name is too long")
        return v.strip()

    @field_validator("state")
    @classmethod
    def validate_state(cls, v: Optional[str]) -> Optional[str]:
        """Валидация штата/региона"""
        if v is None or not v.strip():
            return None
        if len(v) > 50:
            raise ValueError("State name is too long")
        return v.strip()

    @field_validator("zip_code")
    @classmethod
    def validate_zip_code(cls, v: str) -> str:
        """Валидация почтового индекса"""
        if not v.strip():
            raise ValueError("ZIP code cannot be empty")
        # Упрощенная валидация - в реальном проекте можно добавить проверку по форматам разных стран
        cleaned = "".join(c for c in v.strip() if c.isalnum())
        if len(cleaned) < 3 or len(cleaned) > 10:
            raise ValueError("Invalid ZIP code format")
        return cleaned

    @field_validator("country")
    @classmethod
    def validate_country(cls, v: str) -> str:
        """Валидация страны"""
        if not v.strip():
            raise ValueError("Country cannot be empty")
        if len(v) > 50:
            raise ValueError("Country name is too long")
        return v.strip()


class AddressCreate(AddressBase):
    user_id: UUID

    @field_validator("user_id")
    @classmethod
    def validate_user_id(cls, v: UUID) -> UUID:
        """Проверка валидности UUID"""
        if not v:
            raise ValueError("User ID is required")
        return v


class AddressUpdate(BaseModel):
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = None
    is_primary: Optional[bool] = None

    @field_validator("street")
    @classmethod
    def validate_street(cls, v: Optional[str]) -> Optional[str]:
        """Валидация только если поле присутствует"""
        if v is None:
            return None
        if not v.strip():
            raise ValueError("Street cannot be empty")
        if len(v) > 100:
            raise ValueError("Street name is too long")
        return v.strip()

    @field_validator("city")
    @classmethod
    def validate_city(cls, v: Optional[str]) -> Optional[str]:
        """Валидация только если поле присутствует"""
        if v is None:
            return None
        if not v.strip():
            raise ValueError("City cannot be empty")
        if len(v) > 50:
            raise ValueError("City name is too long")
        return v.strip()

    @field_validator("zip_code")
    @classmethod
    def validate_zip_code(cls, v: Optional[str]) -> Optional[str]:
        """Валидация только если поле присутствует"""
        if v is None:
            return None
        if not v.strip():
            raise ValueError("ZIP code cannot be empty")
        cleaned = "".join(c for c in v.strip() if c.isalnum())
        if len(cleaned) < 3 or len(cleaned) > 10:
            raise ValueError("Invalid ZIP code format")
        return cleaned

    @field_validator("country")
    @classmethod
    def validate_country(cls, v: Optional[str]) -> Optional[str]:
        """Валидация только если поле присутствует"""
        if v is None:
            return None
        if not v.strip():
            raise ValueError("Country cannot be empty")
        if len(v) > 50:
            raise ValueError("Country name is too long")
        return v.strip()


class AddressResponse(AddressBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # Для Pydantic v2 (вместо orm_mode=True в v1)
