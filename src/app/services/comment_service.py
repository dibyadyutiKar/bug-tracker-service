"""Comment service."""

from typing import Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    AuthorizationError,
    BusinessRuleError,
    NotFoundError,
)
from app.models.comment import Comment
from app.models.user import User
from app.repositories.comment_repository import CommentRepository
from app.repositories.issue_repository import IssueRepository
from app.schemas.comment import CommentCreate, CommentListParams, CommentUpdate


class CommentService:
    """Comment service for comment management.

    Business Rules:
    - Comments cannot be deleted (audit trail)
    - Only the author can edit their comment
    """

    def __init__(self, session: AsyncSession):
        """Initialize comment service with database session.

        Args:
            session: Async database session
        """
        self.session = session
        self.comment_repo = CommentRepository(session)
        self.issue_repo = IssueRepository(session)

    async def get_comment(self, comment_id: UUID) -> Comment:
        """Get comment by ID with author loaded.

        Args:
            comment_id: Comment UUID

        Returns:
            Comment instance

        Raises:
            NotFoundError: If comment not found
        """
        comment = await self.comment_repo.get_with_author(comment_id)
        if not comment:
            raise NotFoundError("Comment", comment_id)
        return comment

    async def list_comments(
        self,
        issue_id: UUID,
        params: CommentListParams,
    ) -> Tuple[list[Comment], int]:
        """List comments for an issue with pagination.

        Args:
            issue_id: Issue UUID
            params: Query parameters

        Returns:
            Tuple of (comments list, total count)

        Raises:
            NotFoundError: If issue not found
        """
        # Verify issue exists
        issue = await self.issue_repo.get(issue_id)
        if not issue:
            raise NotFoundError("Issue", issue_id)

        return await self.comment_repo.list_by_issue(issue_id, params)

    async def create_comment(
        self,
        issue_id: UUID,
        data: CommentCreate,
        current_user: User,
    ) -> Comment:
        """Create a new comment on an issue.

        Args:
            issue_id: Issue UUID
            data: Comment creation data
            current_user: User creating the comment

        Returns:
            Created comment

        Raises:
            NotFoundError: If issue not found
            BusinessRuleError: If issue's project is archived
        """
        # Get issue with project
        issue = await self.issue_repo.get_with_relations(issue_id)
        if not issue:
            raise NotFoundError("Issue", issue_id)

        # Check if project is archived
        if issue.project.is_archived:
            raise BusinessRuleError(
                "Cannot add comments to issues in archived projects"
            )

        # Create comment
        comment = await self.comment_repo.create({
            "content": data.content,
            "issue_id": issue_id,
            "author_id": current_user.id,
        })

        # Return with author loaded
        return await self.get_comment(comment.id)

    async def update_comment(
        self,
        comment_id: UUID,
        data: CommentUpdate,
        current_user: User,
    ) -> Comment:
        """Update a comment.

        Args:
            comment_id: Comment UUID
            data: Update data
            current_user: User making the update

        Returns:
            Updated comment

        Raises:
            NotFoundError: If comment not found
            AuthorizationError: If user cannot edit this comment
        """
        comment = await self.get_comment(comment_id)

        # Check authorization - only author can edit
        if not comment.can_be_edited_by(current_user):
            raise AuthorizationError(
                "Only the comment author can edit their comment"
            )

        comment = await self.comment_repo.update(comment, {"content": data.content})

        return await self.get_comment(comment.id)

    async def get_comment_count(self, issue_id: UUID) -> int:
        """Get comment count for an issue.

        Args:
            issue_id: Issue UUID

        Returns:
            Number of comments
        """
        return await self.comment_repo.count_by_issue(issue_id)
