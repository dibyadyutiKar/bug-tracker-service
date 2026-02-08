"""Comment schemas."""

from typing import Optional
from uuid import UUID

import bleach
from pydantic import Field, field_validator

from app.schemas.base import BaseResponseSchema, BaseSchema
from app.schemas.user import UserSummary


# Allowed HTML tags for comment content
ALLOWED_TAGS = [
    "p", "br", "strong", "em", "u", "s", "code", "pre",
    "ul", "ol", "li", "blockquote", "a",
]
ALLOWED_ATTRIBUTES = {
    "a": ["href", "title"],
}


def sanitize_content(content: str) -> str:
    """Sanitize comment content to prevent XSS."""
    return bleach.clean(
        content,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        strip=True,
    )


class CommentBase(BaseSchema):
    """Base comment schema."""

    content: str = Field(..., min_length=1, max_length=2000)

    @field_validator("content")
    @classmethod
    def validate_and_sanitize_content(cls, v: str) -> str:
        """Validate content is not empty and sanitize it."""
        if not v.strip():
            raise ValueError("Comment content cannot be empty")
        return sanitize_content(v.strip())


class CommentCreate(CommentBase):
    """Comment creation schema."""

    pass


class CommentUpdate(BaseSchema):
    """Comment update schema."""

    content: str = Field(..., min_length=1, max_length=2000)

    @field_validator("content")
    @classmethod
    def validate_and_sanitize_content(cls, v: str) -> str:
        """Validate content is not empty and sanitize it."""
        if not v.strip():
            raise ValueError("Comment content cannot be empty")
        return sanitize_content(v.strip())


class CommentResponse(BaseResponseSchema, CommentBase):
    """Comment response schema."""

    issue_id: UUID
    author_id: UUID
    author: Optional[UserSummary] = None
    is_edited: bool = False


class CommentListParams(BaseSchema):
    """Comment list query parameters."""

    page: int = Field(1, ge=1)
    limit: int = Field(50, ge=1, le=100)
