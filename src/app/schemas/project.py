"""Project schemas."""

from typing import Optional
from uuid import UUID

from pydantic import Field, field_validator

from app.schemas.base import BaseResponseSchema, BaseSchema
from app.schemas.user import UserSummary


class ProjectBase(BaseSchema):
    """Base project schema."""

    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate project name is not empty after stripping."""
        if not v.strip():
            raise ValueError("Project name cannot be empty")
        return v.strip()


class ProjectCreate(ProjectBase):
    """Project creation schema."""

    pass


class ProjectUpdate(BaseSchema):
    """Project update schema."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate project name if provided."""
        if v is not None and not v.strip():
            raise ValueError("Project name cannot be empty")
        return v.strip() if v else v


class ProjectResponse(BaseResponseSchema, ProjectBase):
    """Project response schema."""

    created_by_id: UUID
    is_archived: bool
    creator: Optional[UserSummary] = None


class ProjectWithStats(ProjectResponse):
    """Project response with statistics."""

    issue_count: int = 0
    open_issue_count: int = 0


class ProjectSummary(BaseSchema):
    """Minimal project info for embedding in other responses."""

    id: UUID
    name: str
    is_archived: bool


class ProjectListParams(BaseSchema):
    """Project list query parameters."""

    search: Optional[str] = None
    is_archived: Optional[bool] = False
    page: int = Field(1, ge=1)
    limit: int = Field(20, ge=1, le=100)
    sort: str = Field("created_at", pattern=r"^-?(name|created_at|updated_at)$")

    @property
    def sort_field(self) -> str:
        """Get sort field name."""
        return self.sort.lstrip("-")

    @property
    def sort_desc(self) -> bool:
        """Check if sort is descending."""
        return self.sort.startswith("-")
