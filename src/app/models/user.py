"""User model."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.models.enums import UserRole

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.issue import Issue
    from app.models.comment import Comment


class User(BaseModel):
    """User model representing system users.

    Attributes:
        username: Unique username (max 50 chars)
        email: Unique email address
        password_hash: Hashed password (Argon2)
        role: User role (developer, manager, admin)
        is_active: Whether user account is active
        last_login: Last login timestamp
    """

    __tablename__ = "users"

    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole),
        default=UserRole.DEVELOPER,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    last_login: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    created_projects: Mapped[list["Project"]] = relationship(
        "Project",
        back_populates="creator",
        foreign_keys="Project.created_by_id",
    )
    reported_issues: Mapped[list["Issue"]] = relationship(
        "Issue",
        back_populates="reporter",
        foreign_keys="Issue.reporter_id",
    )
    assigned_issues: Mapped[list["Issue"]] = relationship(
        "Issue",
        back_populates="assignee",
        foreign_keys="Issue.assignee_id",
    )
    comments: Mapped[list["Comment"]] = relationship(
        "Comment",
        back_populates="author",
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username}, role={self.role})>"

    @property
    def is_admin(self) -> bool:
        """Check if user is an admin."""
        return self.role == UserRole.ADMIN

    @property
    def is_manager(self) -> bool:
        """Check if user is a manager."""
        return self.role == UserRole.MANAGER

    @property
    def is_developer(self) -> bool:
        """Check if user is a developer."""
        return self.role == UserRole.DEVELOPER

    @property
    def can_create_project(self) -> bool:
        """Check if user can create projects."""
        return self.role in (UserRole.MANAGER, UserRole.ADMIN)
