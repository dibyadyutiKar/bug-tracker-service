"""Comment repository."""

from typing import List, Tuple
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.comment import Comment
from app.repositories.base import BaseRepository
from app.schemas.comment import CommentListParams


class CommentRepository(BaseRepository[Comment]):
    """Repository for Comment model operations.

    Note: Comments cannot be deleted (audit trail requirement).
    """

    def __init__(self, session: AsyncSession):
        super().__init__(Comment, session)

    async def delete(self, db_obj: Comment) -> None:
        """Override delete to prevent comment deletion.

        Raises:
            NotImplementedError: Comments cannot be deleted
        """
        raise NotImplementedError(
            "Comments cannot be deleted due to audit trail requirements"
        )

    async def get_with_author(self, id: UUID) -> Comment | None:
        """Get comment with author relationship loaded.

        Args:
            id: Comment UUID

        Returns:
            Comment instance with author loaded or None
        """
        result = await self.session.execute(
            select(Comment)
            .options(selectinload(Comment.author))
            .where(Comment.id == id)
        )
        return result.scalar_one_or_none()

    async def list_by_issue(
        self,
        issue_id: UUID,
        params: CommentListParams,
    ) -> Tuple[List[Comment], int]:
        """List comments for an issue with pagination.

        Args:
            issue_id: Issue UUID
            params: Query parameters

        Returns:
            Tuple of (list of comments, total count)
        """
        # Base query
        query = (
            select(Comment)
            .options(selectinload(Comment.author))
            .where(Comment.issue_id == issue_id)
            .order_by(Comment.created_at.asc())  # Chronological order
        )

        # Count total before pagination
        count_query = (
            select(func.count())
            .select_from(Comment)
            .where(Comment.issue_id == issue_id)
        )
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0

        # Apply pagination
        query = self._apply_pagination(query, params.page, params.limit)

        # Execute query
        result = await self.session.execute(query)
        comments = list(result.scalars().all())

        return comments, total

    async def count_by_issue(self, issue_id: UUID) -> int:
        """Count comments for an issue.

        Args:
            issue_id: Issue UUID

        Returns:
            Comment count
        """
        result = await self.session.execute(
            select(func.count())
            .select_from(Comment)
            .where(Comment.issue_id == issue_id)
        )
        return result.scalar() or 0

    async def get_by_author(
        self,
        author_id: UUID,
        limit: int = 100,
    ) -> List[Comment]:
        """Get comments by author.

        Args:
            author_id: Author user ID
            limit: Maximum number of comments to return

        Returns:
            List of comments
        """
        result = await self.session.execute(
            select(Comment)
            .where(Comment.author_id == author_id)
            .order_by(Comment.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_latest_by_issue(
        self,
        issue_id: UUID,
        limit: int = 5,
    ) -> List[Comment]:
        """Get latest comments for an issue.

        Args:
            issue_id: Issue UUID
            limit: Maximum number of comments to return

        Returns:
            List of latest comments
        """
        result = await self.session.execute(
            select(Comment)
            .options(selectinload(Comment.author))
            .where(Comment.issue_id == issue_id)
            .order_by(Comment.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
