"""Project model."""

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.issue import Issue


class Project(BaseModel):
    """Project model representing a software project.

    Attributes:
        name: Unique project name (max 100 chars)
        description: Optional project description (max 1000 chars)
        created_by_id: ID of the user who created the project
        is_archived: Soft delete flag
    """

    __tablename__ = "projects"

    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    created_by_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="PROTECT"),
        nullable=False,
    )
    is_archived: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
    )

    # Relationships
    creator: Mapped["User"] = relationship(
        "User",
        back_populates="created_projects",
        foreign_keys=[created_by_id],
    )
    issues: Mapped[list["Issue"]] = relationship(
        "Issue",
        back_populates="project",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Project(id={self.id}, name={self.name}, archived={self.is_archived})>"

    def can_be_modified_by(self, user: "User") -> bool:
        """Check if user can modify this project.

        Only the creator or admin can modify/archive a project.
        """
        from app.models.enums import UserRole

        if user.role == UserRole.ADMIN:
            return True
        return self.created_by_id == user.id

    @property
    def issue_count(self) -> int:
        """Get total number of issues."""
        return len(self.issues) if self.issues else 0

    @property
    def open_issue_count(self) -> int:
        """Get number of open issues."""
        from app.models.enums import IssueStatus

        if not self.issues:
            return 0
        return sum(
            1 for issue in self.issues
            if issue.status in (IssueStatus.OPEN, IssueStatus.IN_PROGRESS, IssueStatus.REOPENED)
        )
