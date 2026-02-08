"""Base Pydantic schemas."""

from datetime import datetime
from typing import Generic, List, Optional, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    """Base schema with common configuration."""

    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=True,
        validate_assignment=True,
    )


class TimestampSchema(BaseSchema):
    """Schema with timestamp fields."""

    created_at: datetime
    updated_at: datetime


class IDSchema(BaseSchema):
    """Schema with ID field."""

    id: UUID


class BaseResponseSchema(IDSchema, TimestampSchema):
    """Base response schema with id and timestamps."""

    pass


# Generic type for pagination
T = TypeVar("T")


class PaginatedResponse(BaseSchema, Generic[T]):
    """Paginated response schema."""

    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int

    @property
    def has_next(self) -> bool:
        """Check if there's a next page."""
        return self.page < self.total_pages

    @property
    def has_prev(self) -> bool:
        """Check if there's a previous page."""
        return self.page > 1


class ErrorDetail(BaseSchema):
    """Error detail schema."""

    field: Optional[str] = None
    message: str


class ErrorResponse(BaseSchema):
    """Error response schema."""

    code: str
    message: str
    errors: List[ErrorDetail] = []
    request_id: Optional[str] = None
