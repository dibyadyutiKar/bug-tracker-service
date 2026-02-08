"""Issue service with state machine for status transitions."""

from typing import Optional, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    AuthorizationError,
    BusinessRuleError,
    InvalidStateTransitionError,
    NotFoundError,
)
from app.models.issue import Issue
from app.models.user import User
from app.models.enums import IssuePriority, IssueStatus, UserRole
from app.repositories.issue_repository import IssueRepository
from app.repositories.project_repository import ProjectRepository
from app.schemas.issue import IssueCreate, IssueListParams, IssueUpdate


class IssueService:
    """Issue service for issue management with status state machine."""

    def __init__(self, session: AsyncSession):
        """Initialize issue service with database session.

        Args:
            session: Async database session
        """
        self.session = session
        self.issue_repo = IssueRepository(session)
        self.project_repo = ProjectRepository(session)

    async def get_issue(self, issue_id: UUID) -> Issue:
        """Get issue by ID with all relations loaded.

        Args:
            issue_id: Issue UUID

        Returns:
            Issue instance

        Raises:
            NotFoundError: If issue not found
        """
        issue = await self.issue_repo.get_with_relations(issue_id)
        if not issue:
            raise NotFoundError("Issue", issue_id)
        return issue

    async def list_issues(
        self,
        project_id: UUID,
        params: IssueListParams,
    ) -> Tuple[list[Issue], int]:
        """List issues for a project with filtering and pagination.

        Args:
            project_id: Project UUID
            params: Query parameters

        Returns:
            Tuple of (issues list, total count)

        Raises:
            NotFoundError: If project not found
        """
        # Verify project exists
        project = await self.project_repo.get(project_id)
        if not project:
            raise NotFoundError("Project", project_id)

        return await self.issue_repo.list_by_project(project_id, params)

    async def create_issue(
        self,
        project_id: UUID,
        data: IssueCreate,
        current_user: User,
    ) -> Issue:
        """Create a new issue.

        Args:
            project_id: Project UUID
            data: Issue creation data
            current_user: User creating the issue

        Returns:
            Created issue

        Raises:
            NotFoundError: If project not found
        """
        # Verify project exists and is not archived
        project = await self.project_repo.get(project_id)
        if not project:
            raise NotFoundError("Project", project_id)
        if project.is_archived:
            raise BusinessRuleError("Cannot create issues in an archived project")

        # Create issue
        issue = await self.issue_repo.create({
            "title": data.title,
            "description": data.description,
            "priority": data.priority,
            "due_date": data.due_date,
            "status": IssueStatus.OPEN,
            "project_id": project_id,
            "reporter_id": current_user.id,
            "assignee_id": data.assignee_id,
        })

        # Return with relations loaded
        return await self.get_issue(issue.id)

    async def update_issue(
        self,
        issue_id: UUID,
        data: IssueUpdate,
        current_user: User,
    ) -> Issue:
        """Update an issue.

        Args:
            issue_id: Issue UUID
            data: Update data
            current_user: User making the update

        Returns:
            Updated issue

        Raises:
            NotFoundError: If issue not found
            AuthorizationError: If user cannot update this issue
            InvalidStateTransitionError: If status transition is invalid
            BusinessRuleError: If business rules are violated
        """
        issue = await self.get_issue(issue_id)

        # Check authorization
        self._check_modify_permission(issue, current_user, data)

        # Handle status transition if changing status
        if data.status and data.status != issue.status:
            await self._validate_status_transition(issue, data.status)

        # Filter out None values
        update_data = {k: v for k, v in data.model_dump().items() if v is not None}

        if update_data:
            issue = await self.issue_repo.update(issue, update_data)

        # Return with relations loaded
        return await self.get_issue(issue.id)

    async def change_status(
        self,
        issue_id: UUID,
        new_status: IssueStatus,
        current_user: User,
    ) -> Issue:
        """Change issue status following state machine rules.

        Args:
            issue_id: Issue UUID
            new_status: Target status
            current_user: User making the change

        Returns:
            Updated issue

        Raises:
            NotFoundError: If issue not found
            AuthorizationError: If user cannot change status
            InvalidStateTransitionError: If transition is invalid
            BusinessRuleError: If business rules are violated
        """
        issue = await self.get_issue(issue_id)

        # Check authorization
        self._check_modify_permission(issue, current_user)

        # Validate transition
        await self._validate_status_transition(issue, new_status)

        # Update status
        issue = await self.issue_repo.update(issue, {"status": new_status})

        return await self.get_issue(issue.id)

    async def assign_issue(
        self,
        issue_id: UUID,
        assignee_id: Optional[UUID],
        current_user: User,
    ) -> Issue:
        """Assign or unassign an issue.

        Args:
            issue_id: Issue UUID
            assignee_id: User UUID to assign, or None to unassign
            current_user: User making the assignment

        Returns:
            Updated issue

        Raises:
            NotFoundError: If issue not found
            AuthorizationError: If user cannot change assignee
        """
        issue = await self.get_issue(issue_id)

        # Check authorization - only reporter, manager, or admin can change assignee
        self._check_assignee_permission(issue, current_user)

        issue = await self.issue_repo.update(issue, {"assignee_id": assignee_id})

        return await self.get_issue(issue.id)

    async def _validate_status_transition(
        self,
        issue: Issue,
        target_status: IssueStatus,
    ) -> None:
        """Validate status transition against state machine.

        Args:
            issue: Current issue
            target_status: Target status

        Raises:
            InvalidStateTransitionError: If transition is invalid
            BusinessRuleError: If business rules are violated
        """
        # Check if transition is valid according to state machine
        if not issue.can_transition_to(target_status):
            raise InvalidStateTransitionError(
                issue.status.value,
                target_status.value,
            )

        # Business rule: Critical issues cannot be closed without comments
        if target_status == IssueStatus.CLOSED:
            if issue.priority == IssuePriority.CRITICAL:
                comment_count = len(issue.comments) if issue.comments else 0
                if comment_count == 0:
                    raise BusinessRuleError(
                        "Critical issues must have at least one comment before closing"
                    )

    def _check_modify_permission(
        self,
        issue: Issue,
        user: User,
        data: Optional[IssueUpdate] = None,
    ) -> None:
        """Check if user can modify an issue.

        Args:
            issue: Issue instance
            user: User to check
            data: Optional update data to check specific field permissions

        Raises:
            AuthorizationError: If user cannot modify the issue
        """
        # Admins and managers can modify any issue
        if user.role in (UserRole.ADMIN, UserRole.MANAGER):
            return

        # Reporter can modify their reported issue
        if issue.reporter_id == user.id:
            return

        # Assignee can modify assigned issue
        if issue.assignee_id and issue.assignee_id == user.id:
            return

        raise AuthorizationError(
            "Only the reporter, assignee, manager, or admin can modify this issue"
        )

    def _check_assignee_permission(
        self,
        issue: Issue,
        user: User,
    ) -> None:
        """Check if user can change issue assignee.

        Args:
            issue: Issue instance
            user: User to check

        Raises:
            AuthorizationError: If user cannot change assignee
        """
        # Admins and managers can change assignee
        if user.role in (UserRole.ADMIN, UserRole.MANAGER):
            return

        # Reporter can change assignee
        if issue.reporter_id == user.id:
            return

        raise AuthorizationError(
            "Only the reporter, manager, or admin can change the assignee"
        )
