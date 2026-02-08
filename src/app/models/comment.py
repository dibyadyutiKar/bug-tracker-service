"""Comment model."""

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.issue import Issue


class Comment(BaseModel):
    """Comment model for issue comments.

    Attributes:
        content: Comment content (max 2000 chars, required, non-empty)
        issue_id: Associated issue ID
        author_id: ID of user who wrote the comment

    Business Rules:
        - Comments cannot be deleted (audit trail)
        - Only the author can edit their comment
    """

    __tablename__ = "comments"

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    issue_id: Mapped[UUID] = mapped_column(
        ForeignKey("issues.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    author_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="PROTECT"),
        nullable=False,
        index=True,
    )

    # Relationships
    issue: Mapped["Issue"] = relationship(
        "Issue",
        back_populates="comments",
    )
    author: Mapped["User"] = relationship(
        "User",
        back_populates="comments",
    )

    def __repr__(self) -> str:
        content_preview = self.content[:30] + "..." if len(self.content) > 30 else self.content
        return f"<Comment(id={self.id}, content={content_preview})>"

    def can_be_edited_by(self, user: "User") -> bool:
        """Check if user can edit this comment.

        Only the author can edit their own comment.
        """
        return self.author_id == user.id

    @property
    def is_edited(self) -> bool:
        """Check if comment has been edited."""
        return self.updated_at > self.created_at
