"""Issue API endpoints."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import CurrentUser, DBSession
from app.core.exceptions import (
    AuthorizationError,
    BusinessRuleError,
    InvalidStateTransitionError,
    NotFoundError,
)
from app.models.enums import IssuePriority, IssueStatus
from app.schemas.base import PaginatedResponse
from app.schemas.issue import (
    IssueCreate,
    IssueDetail,
    IssueListParams,
    IssueResponse,
    IssueStatusUpdate,
    IssueUpdate,
)
from app.services.issue_service import IssueService

router = APIRouter(tags=["Issues"])


@router.get(
    "/projects/{project_id}/issues",
    response_model=PaginatedResponse[IssueResponse],
    summary="List project issues",
    description="Get list of issues for a project with filtering and pagination.",
)
async def list_project_issues(
    project_id: UUID,
    db: DBSession,
    current_user: CurrentUser,
    status_filter: Optional[IssueStatus] = Query(
        None, alias="status", description="Filter by status"
    ),
    priority: Optional[IssuePriority] = Query(None, description="Filter by priority"),
    assignee_id: Optional[UUID] = Query(None, description="Filter by assignee"),
    search: Optional[str] = Query(None, description="Search in title and description"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    sort: str = Query(
        "-created_at",
        pattern=r"^-?(title|status|priority|created_at|updated_at|due_date)$",
        description="Sort field (prefix with - for descending)",
    ),
):
    """List issues for a project."""
    params = IssueListParams(
        status=status_filter,
        priority=priority,
        assignee_id=assignee_id,
        search=search,
        page=page,
        limit=limit,
        sort=sort,
    )

    try:
        issue_service = IssueService(db)
        issues, total = await issue_service.list_issues(project_id, params)

        total_pages = (total + limit - 1) // limit

        return PaginatedResponse(
            items=[IssueResponse.model_validate(i) for i in issues],
            total=total,
            page=page,
            page_size=limit,
            total_pages=total_pages,
        )
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )


@router.post(
    "/projects/{project_id}/issues",
    response_model=IssueResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create issue",
    description="Create a new issue in a project.",
)
async def create_issue(
    project_id: UUID,
    data: IssueCreate,
    db: DBSession,
    current_user: CurrentUser,
):
    """Create a new issue."""
    try:
        issue_service = IssueService(db)
        issue = await issue_service.create_issue(project_id, data, current_user)
        return issue
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )
    except BusinessRuleError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        )


@router.get(
    "/issues/{issue_id}",
    response_model=IssueDetail,
    summary="Get issue details",
    description="Get detailed issue information with all relations.",
)
async def get_issue(
    issue_id: UUID,
    db: DBSession,
    current_user: CurrentUser,
):
    """Get issue by ID."""
    try:
        issue_service = IssueService(db)
        issue = await issue_service.get_issue(issue_id)

        response = IssueDetail.model_validate(issue)
        response.comment_count = issue.comment_count

        return response
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )


@router.patch(
    "/issues/{issue_id}",
    response_model=IssueResponse,
    summary="Update issue",
    description="Update issue details. Requires reporter, assignee, or manager/admin role.",
)
async def update_issue(
    issue_id: UUID,
    data: IssueUpdate,
    db: DBSession,
    current_user: CurrentUser,
):
    """Update an issue."""
    try:
        issue_service = IssueService(db)
        issue = await issue_service.update_issue(issue_id, data, current_user)
        return issue
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )
    except AuthorizationError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=e.message,
        )
    except InvalidStateTransitionError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        )
    except BusinessRuleError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        )


@router.patch(
    "/issues/{issue_id}/status",
    response_model=IssueResponse,
    summary="Change issue status",
    description="Change issue status following state machine rules.",
)
async def change_issue_status(
    issue_id: UUID,
    data: IssueStatusUpdate,
    db: DBSession,
    current_user: CurrentUser,
):
    """Change issue status."""
    try:
        issue_service = IssueService(db)
        issue = await issue_service.change_status(
            issue_id, data.status, current_user
        )
        return issue
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )
    except AuthorizationError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=e.message,
        )
    except InvalidStateTransitionError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        )
    except BusinessRuleError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        )


@router.patch(
    "/issues/{issue_id}/assign",
    response_model=IssueResponse,
    summary="Assign issue",
    description="Assign or unassign an issue. Requires reporter or manager/admin role.",
)
async def assign_issue(
    issue_id: UUID,
    assignee_id: Optional[UUID] = Query(
        None, description="User ID to assign, or null to unassign"
    ),
    db: DBSession = None,
    current_user: CurrentUser = None,
):
    """Assign or unassign an issue."""
    try:
        issue_service = IssueService(db)
        issue = await issue_service.assign_issue(issue_id, assignee_id, current_user)
        return issue
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )
    except AuthorizationError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=e.message,
        )
