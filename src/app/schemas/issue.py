"""Issue schemas."""

from datetime import date
from typing import Optional
from uuid import UUID

import bleach
from pydantic import Field, field_validator

from app.models.enums import IssuePriority, IssueStatus
from app.schemas.base import BaseResponseSchema, BaseSchema
from app.schemas.user import UserSummary
from app.schemas.project import ProjectSummary


# Allowed HTML tags for markdown content
ALLOWED_TAGS = [
    "p", "br", "strong", "em", "u", "s", "code", "pre",
    "h1", "h2", "h3", "h4", "h5", "h6",
    "ul", "ol", "li", "blockquote", "a", "img",
    "table", "thead", "tbody", "tr", "th", "td",
]
ALLOWED_ATTRIBUTES = {
    "a": ["href", "title"],
    "img": ["src", "alt", "title"],
}


def sanitize_markdown(content: str) -> str:
    """Sanitize markdown/HTML content to prevent XSS."""
    return bleach.clean(
        content,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        strip=True,
    )


class IssueBase(BaseSchema):
    """Base issue schema."""

    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=5000)
    priority: IssuePriority = IssuePriority.MEDIUM
    due_date: Optional[date] = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        """Validate title is not empty."""
        if not v.strip():
            raise ValueError("Issue title cannot be empty")
        return v.strip()

    @field_validator("description")
    @classmethod
    def sanitize_description(cls, v: Optional[str]) -> Optional[str]:
        """Sanitize description to prevent XSS."""
        if v is not None:
            return sanitize_markdown(v)
        return v


class IssueCreate(IssueBase):
    """Issue creation schema."""

    assignee_id: Optional[UUID] = None


class IssueUpdate(BaseSchema):
    """Issue update schema."""

    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=5000)
    status: Optional[IssueStatus] = None
    priority: Optional[IssuePriority] = None
    assignee_id: Optional[UUID] = None
    due_date: Optional[date] = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: Optional[str]) -> Optional[str]:
        """Validate title if provided."""
        if v is not None and not v.strip():
            raise ValueError("Issue title cannot be empty")
        return v.strip() if v else v

    @field_validator("description")
    @classmethod
    def sanitize_description(cls, v: Optional[str]) -> Optional[str]:
        """Sanitize description to prevent XSS."""
        if v is not None:
            return sanitize_markdown(v)
        return v


class IssueResponse(BaseResponseSchema, IssueBase):
    """Issue response schema."""

    status: IssueStatus
    project_id: UUID
    reporter_id: UUID
    assignee_id: Optional[UUID] = None

    # Embedded relations
    project: Optional[ProjectSummary] = None
    reporter: Optional[UserSummary] = None
    assignee: Optional[UserSummary] = None
    comment_count: int = 0


class IssueDetail(IssueResponse):
    """Detailed issue response with all relations."""

    pass


class IssueSummary(BaseSchema):
    """Minimal issue info for embedding."""

    id: UUID
    title: str
    status: IssueStatus
    priority: IssuePriority


class IssueListParams(BaseSchema):
    """Issue list query parameters."""

    status: Optional[IssueStatus] = None
    priority: Optional[IssuePriority] = None
    assignee_id: Optional[UUID] = None
    reporter_id: Optional[UUID] = None
    search: Optional[str] = None
    page: int = Field(1, ge=1)
    limit: int = Field(20, ge=1, le=100)
    sort: str = Field(
        "-created_at",
        pattern=r"^-?(title|status|priority|created_at|updated_at|due_date)$"
    )

    @property
    def sort_field(self) -> str:
        """Get sort field name."""
        return self.sort.lstrip("-")

    @property
    def sort_desc(self) -> bool:
        """Check if sort is descending."""
        return self.sort.startswith("-")


class IssueStatusUpdate(BaseSchema):
    """Schema for updating issue status."""

    status: IssueStatus
