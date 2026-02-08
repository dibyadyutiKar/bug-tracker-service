"""Issue repository."""

from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.issue import Issue
from app.models.enums import IssuePriority, IssueStatus
from app.repositories.base import BaseRepository
from app.schemas.issue import IssueListParams


class IssueRepository(BaseRepository[Issue]):
    """Repository for Issue model operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(Issue, session)

    async def get_with_relations(self, id: UUID) -> Optional[Issue]:
        """Get issue with all relationships loaded.

        Args:
            id: Issue UUID

        Returns:
            Issue instance with relations loaded or None
        """
        result = await self.session.execute(
            select(Issue)
            .options(
                selectinload(Issue.project),
                selectinload(Issue.reporter),
                selectinload(Issue.assignee),
                selectinload(Issue.comments),
            )
            .where(Issue.id == id)
        )
        return result.scalar_one_or_none()

    async def list_by_project(
        self,
        project_id: UUID,
        params: IssueListParams,
    ) -> Tuple[List[Issue], int]:
        """List issues for a project with filtering, sorting, and pagination.

        Args:
            project_id: Project UUID
            params: Query parameters

        Returns:
            Tuple of (list of issues, total count)
        """
        # Base query
        query = (
            select(Issue)
            .options(
                selectinload(Issue.project),
                selectinload(Issue.reporter),
                selectinload(Issue.assignee),
                selectinload(Issue.comments),
            )
            .where(Issue.project_id == project_id)
        )

        # Apply filters
        if params.status:
            query = query.where(Issue.status == params.status)
        if params.priority:
            query = query.where(Issue.priority == params.priority)
        if params.assignee_id:
            query = query.where(Issue.assignee_id == params.assignee_id)
        if params.reporter_id:
            query = query.where(Issue.reporter_id == params.reporter_id)
        if params.search:
            search_term = f"%{params.search}%"
            query = query.where(
                or_(
                    Issue.title.ilike(search_term),
                    Issue.description.ilike(search_term),
                )
            )

        # Count total before pagination
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0

        # Apply sorting
        query = self._apply_sorting(query, params.sort_field, params.sort_desc)

        # Apply pagination
        query = self._apply_pagination(query, params.page, params.limit)

        # Execute query
        result = await self.session.execute(query)
        issues = list(result.scalars().all())

        return issues, total

    async def get_by_assignee(
        self,
        assignee_id: UUID,
        status: Optional[IssueStatus] = None,
    ) -> List[Issue]:
        """Get issues assigned to a user.

        Args:
            assignee_id: Assignee user ID
            status: Optional status filter

        Returns:
            List of issues
        """
        query = select(Issue).where(Issue.assignee_id == assignee_id)
        if status:
            query = query.where(Issue.status == status)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_reporter(
        self,
        reporter_id: UUID,
        status: Optional[IssueStatus] = None,
    ) -> List[Issue]:
        """Get issues reported by a user.

        Args:
            reporter_id: Reporter user ID
            status: Optional status filter

        Returns:
            List of issues
        """
        query = select(Issue).where(Issue.reporter_id == reporter_id)
        if status:
            query = query.where(Issue.status == status)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_by_project(
        self,
        project_id: UUID,
        status: Optional[IssueStatus] = None,
    ) -> int:
        """Count issues in a project.

        Args:
            project_id: Project UUID
            status: Optional status filter

        Returns:
            Issue count
        """
        query = (
            select(func.count())
            .select_from(Issue)
            .where(Issue.project_id == project_id)
        )
        if status:
            query = query.where(Issue.status == status)
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def count_by_priority(
        self,
        project_id: UUID,
        priority: IssuePriority,
    ) -> int:
        """Count issues by priority in a project.

        Args:
            project_id: Project UUID
            priority: Priority level

        Returns:
            Issue count
        """
        result = await self.session.execute(
            select(func.count())
            .select_from(Issue)
            .where(Issue.project_id == project_id)
            .where(Issue.priority == priority)
        )
        return result.scalar() or 0

    async def get_open_issues(self, project_id: UUID) -> List[Issue]:
        """Get all open issues in a project.

        Args:
            project_id: Project UUID

        Returns:
            List of open issues
        """
        open_statuses = [
            IssueStatus.OPEN,
            IssueStatus.IN_PROGRESS,
            IssueStatus.REOPENED,
        ]
        result = await self.session.execute(
            select(Issue)
            .where(Issue.project_id == project_id)
            .where(Issue.status.in_(open_statuses))
        )
        return list(result.scalars().all())

    async def get_overdue_issues(self, project_id: UUID) -> List[Issue]:
        """Get overdue issues (past due date and not closed).

        Args:
            project_id: Project UUID

        Returns:
            List of overdue issues
        """
        from datetime import date

        closed_statuses = [IssueStatus.CLOSED, IssueStatus.RESOLVED]
        result = await self.session.execute(
            select(Issue)
            .where(Issue.project_id == project_id)
            .where(Issue.due_date < date.today())
            .where(~Issue.status.in_(closed_statuses))
        )
        return list(result.scalars().all())
