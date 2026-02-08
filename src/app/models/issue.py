"""Issue model."""

from datetime import date
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import Date, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.models.enums import IssuePriority, IssueStatus

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.project import Project
    from app.models.comment import Comment


class Issue(BaseModel):
    """Issue model representing a bug or task.

    Attributes:
        title: Issue title (max 200 chars)
        description: Detailed description (max 5000 chars, markdown supported)
        status: Current status (follows state machine)
        priority: Issue priority level
        project_id: Associated project ID
        reporter_id: ID of user who reported the issue
        assignee_id: ID of user assigned to the issue (optional)
        due_date: Optional due date

    Business Rules:
        - Status transitions must follow the state machine
        - Critical issues cannot be closed without at least one comment
    """

    __tablename__ = "issues"

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    status: Mapped[IssueStatus] = mapped_column(
        Enum(IssueStatus),
        default=IssueStatus.OPEN,
        nullable=False,
        index=True,
    )
    priority: Mapped[IssuePriority] = mapped_column(
        Enum(IssuePriority),
        default=IssuePriority.MEDIUM,
        nullable=False,
        index=True,
    )
    project_id: Mapped[UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    reporter_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="PROTECT"),
        nullable=False,
        index=True,
    )
    assignee_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    due_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )

    # Relationships
    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="issues",
    )
    reporter: Mapped["User"] = relationship(
        "User",
        back_populates="reported_issues",
        foreign_keys=[reporter_id],
    )
    assignee: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="assigned_issues",
        foreign_keys=[assignee_id],
    )
    comments: Mapped[list["Comment"]] = relationship(
        "Comment",
        back_populates="issue",
        cascade="all, delete-orphan",
        order_by="Comment.created_at",
    )

    def __repr__(self) -> str:
        return f"<Issue(id={self.id}, title={self.title[:30]}..., status={self.status})>"

    def can_transition_to(self, target_status: IssueStatus) -> bool:
        """Check if transition to target status is valid."""
        return self.status.can_transition_to(target_status)

    def can_be_closed(self) -> bool:
        """Check if issue can be closed.

        Critical issues require at least one comment before closing.
        """
        if self.priority == IssuePriority.CRITICAL:
            return len(self.comments) > 0 if self.comments else False
        return True

    def can_be_modified_by(self, user: "User") -> bool:
        """Check if user can modify this issue.

        Reporter, assignee, project owner, manager, or admin can modify.
        """
        from app.models.enums import UserRole

        if user.role in (UserRole.MANAGER, UserRole.ADMIN):
            return True
        if self.reporter_id == user.id:
            return True
        if self.assignee_id and self.assignee_id == user.id:
            return True
        return False

    @property
    def is_open(self) -> bool:
        """Check if issue is in an open state."""
        return self.status in (
            IssueStatus.OPEN,
            IssueStatus.IN_PROGRESS,
            IssueStatus.REOPENED,
        )

    @property
    def is_resolved(self) -> bool:
        """Check if issue is resolved or closed."""
        return self.status in (IssueStatus.RESOLVED, IssueStatus.CLOSED)

    @property
    def comment_count(self) -> int:
        """Get number of comments."""
        return len(self.comments) if self.comments else 0
