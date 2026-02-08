"""User schemas."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import EmailStr, Field

from app.models.enums import UserRole
from app.schemas.base import BaseResponseSchema, BaseSchema


class UserBase(BaseSchema):
    """Base user schema."""

    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr


class UserCreate(UserBase):
    """User creation schema (internal use)."""

    password_hash: str
    role: UserRole = UserRole.DEVELOPER


class UserUpdate(BaseSchema):
    """User update schema."""

    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class UserResponse(BaseResponseSchema, UserBase):
    """User response schema (public)."""

    role: UserRole
    is_active: bool
    last_login: Optional[datetime] = None


class UserProfile(UserResponse):
    """Current user profile schema."""

    pass


class UserSummary(BaseSchema):
    """Minimal user info for embedding in other responses."""

    id: UUID
    username: str
    email: EmailStr
