from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, field_validator


class AddressBase(BaseModel):
    street: str
    city: str
    state: str
    zip_code: str
    country: str
    is_primary: bool = False


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    description: Optional[str] = None

    @field_validator("username")
    @classmethod
    def validate_username(cls, v):
        if len(v) < 3:
            raise ValueError("Username must be at least 3 characters")
        return v


class UserUpdate(BaseModel):
    username: Optional[str] = None
    description: Optional[str] = None

    @field_validator("username")
    @classmethod
    def validate_username(cls, v):
        if v is not None and len(v) < 3:
            raise ValueError("Username must be at least 3 characters")
        return v


class UserResponse(BaseModel):
    id: UUID
    username: str
    email: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    addresses: List[AddressBase] = []

    class Config:
        from_attributes = True
